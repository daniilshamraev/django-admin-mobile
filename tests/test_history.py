import json
from datetime import timedelta

import pytest
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from admin_mobile.history import history_count, history_groups
from library.models import Author, Book

pytestmark = pytest.mark.django_db


def test_history_groups_are_newest_first_and_split_by_day() -> None:
    user_model = get_user_model()
    user = user_model.objects.create_superuser("hist", "hist@example.com", "secret")
    author = Author.objects.create(name="Ada Lovelace")
    book = Book.objects.create(
        title="Notes", author=author, status=Book.Status.DRAFT
    )
    content_type = ContentType.objects.get_for_model(book)
    now = timezone.now()
    specs = (
        (now - timedelta(days=2, hours=4), ADDITION, "Added."),
        (
            now - timedelta(days=2, hours=1),
            CHANGE,
            json.dumps([{"changed": {"fields": ["Title", "Status"]}}]),
        ),
        (
            now - timedelta(days=1, hours=2),
            CHANGE,
            json.dumps([{"changed": {"fields": ["Pages"]}}]),
        ),
        (now - timedelta(days=1, hours=1), DELETION, "Deleted chapter."),
    )
    for when, flag, message in specs:
        LogEntry.objects.create(
            user_id=user.pk,
            content_type_id=content_type.pk,
            object_id=str(book.pk),
            object_repr=str(book),
            action_flag=flag,
            change_message=message,
            action_time=when,
        )
    entries = LogEntry.objects.filter(object_id=str(book.pk))
    groups = history_groups(entries)
    assert len(groups) == 2
    newest = groups[0]["items"]
    assert isinstance(newest, list)
    assert newest[0]["kind"] == "deleted"
    assert newest[1]["kind"] == "changed"
    assert newest[1]["fields"] == ["Pages"]
    older = groups[1]["items"]
    assert isinstance(older, list)
    assert older[-1]["kind"] == "added"
    changed = older[0]
    assert changed["fields"] == ["Title", "Status"]
    assert "Changed" in str(changed["title"])
    assert history_count(entries) == 4


def test_empty_history_page_has_a_phone_empty_state(client: Client) -> None:
    user_model = get_user_model()
    user = user_model.objects.create_superuser("hist2", "h2@example.com", "secret")
    author = Author.objects.create(name="Grace Hopper")
    book = Book.objects.create(
        title="Compiler", author=author, status=Book.Status.DRAFT
    )
    client.force_login(user)
    response = client.get(reverse("admin:library_book_history", args=[book.pk]))
    html = response.content.decode()
    assert response.status_code == 200
    assert "No history yet" in html
    assert "admin-mobile-history-empty" in html
