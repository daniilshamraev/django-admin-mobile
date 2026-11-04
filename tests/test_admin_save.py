from datetime import date, datetime, time, timezone

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone as dj_tz

from library.models import Author, Book, Chapter
from tests.formparse import admin_form_data

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client() -> Client:
    user_model = get_user_model()
    user = user_model.objects.create_superuser("editor", "editor@example.com", "secret")
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def author() -> Author:
    return Author.objects.create(name="Grace Hopper", birth_date=date(1906, 12, 9))


def test_change_form_renders_native_inputs(
    admin_client: Client,
    author: Author,
) -> None:
    book = Book.objects.create(title="Draft", author=author, pages=12)
    Chapter.objects.create(book=book, title="A-0", order=1, starts_at=time(8, 0))
    response = admin_client.get(reverse("admin:library_book_change", args=[book.pk]))
    html = response.content.decode()
    assert response.status_code == 200
    assert 'type="date"' in html
    assert 'type="time"' in html
    assert "admin-mobile-split" in html
    assert "Europe/Moscow" in html


def test_change_form_saves_native_values_in_current_timezone(
    admin_client: Client,
    author: Author,
) -> None:
    book = Book.objects.create(title="Draft", author=author, pages=12)
    url = reverse("admin:library_book_change", args=[book.pk])
    response = admin_client.get(url)
    data = admin_form_data(response.content.decode())
    data.update(
        {
            "title": "Draft",
            "author": str(author.pk),
            "status": Book.Status.PUBLISHED,
            "pages": "240",
            "published_on": "1952-05-03",
            "reading_time": "07:45:00",
            "scheduled_for_0": "2024-06-15",
            "scheduled_for_1": "15:00:00",
            "notes": "Kept the native inputs.",
            "_save": "Save",
        }
    )
    saved = admin_client.post(url, data)
    assert saved.status_code == 302, saved.content.decode()[:1500]
    book.refresh_from_db()
    assert book.published_on == date(1952, 5, 3)
    assert book.reading_time == time(7, 45)
    assert book.status == Book.Status.PUBLISHED
    assert dj_tz.is_aware(book.scheduled_for)
    assert book.scheduled_for.astimezone(timezone.utc) == datetime(
        2024, 6, 15, 12, 0, tzinfo=timezone.utc
    )


def test_change_form_rejects_a_bad_date(
    admin_client: Client,
    author: Author,
) -> None:
    book = Book.objects.create(title="Draft", author=author)
    url = reverse("admin:library_book_change", args=[book.pk])
    response = admin_client.get(url)
    data = admin_form_data(response.content.decode())
    data["published_on"] = "03.05.1952"
    data["title"] = "Draft"
    data["_save"] = "Save"
    saved = admin_client.post(url, data)
    assert saved.status_code == 200
    book.refresh_from_db()
    assert book.published_on is None
