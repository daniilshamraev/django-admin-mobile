import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings

from library.demo import seed_demo
from library.models import Author, Book

pytestmark = pytest.mark.django_db


def test_seed_stays_off_without_demo_flag() -> None:
    assert seed_demo() is False
    assert Author.objects.exists() is False


@override_settings(DEBUG=True, ADMIN_MOBILE_DEMO=True)
def test_seed_is_idempotent_and_local_only() -> None:
    assert seed_demo() is True
    assert seed_demo() is False
    assert Book.objects.count() == 4
    user_model = get_user_model()
    user = user_model.objects.get(username="admin")
    assert user.check_password("admin") is True
    assert user.is_superuser is True


@override_settings(DEBUG=False, ADMIN_MOBILE_DEMO=True)
def test_seed_refuses_when_debug_is_off() -> None:
    assert seed_demo() is False
    assert Author.objects.exists() is False
