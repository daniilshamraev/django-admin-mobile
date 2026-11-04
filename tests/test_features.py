import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings
from django.urls import reverse

from admin_mobile.colors import accent_declarations, sanitize_hex
from admin_mobile.conf import get_config
from admin_mobile.readonly import readonly_blocks
from admin_mobile.search import clean_query
from library.models import Book, Tag

pytestmark = pytest.mark.django_db


def test_hex_rejects_css_injection() -> None:
    assert sanitize_hex("#205067") == "#205067"
    assert sanitize_hex("#abc") == "#abc"
    assert sanitize_hex("red;background:url(https://evil)") is None
    assert sanitize_hex("expression(alert(1))") is None
    assert "expression" not in accent_declarations(None, (("primary", "#112233"),))


def test_accent_style_targets_both_themes() -> None:
    css = accent_declarations("#205067", ())
    assert "html[data-theme='dark']" in css
    assert "prefers-color-scheme: dark" in css
    assert "--button-bg:#205067" in css
    assert "--accent:" not in css
    assert "--header-bg" not in css
    assert "--body-bg" not in css


@override_settings(
    ADMIN_MOBILE={
        "ACCENT": "#205067",
        "UNDO_SECONDS": 6,
        "READONLY_MODELS": ["library.tag"],
    }
)
def test_non_bool_settings_are_typed() -> None:
    config = get_config()
    assert config.accent == "#205067"
    assert config.undo_seconds == 6
    assert config.readonly_models == ("library.tag",)
    assert config.undo_delete is False


@override_settings(ADMIN_MOBILE={"ACCENT": "blue"})
def test_bad_accent_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="hex"):
        get_config()


@override_settings(ADMIN_MOBILE={"UNDO_SECONDS": 3})
def test_undo_window_is_bounded() -> None:
    with pytest.raises(ImproperlyConfigured, match="5 to 10"):
        get_config()


@override_settings(ADMIN_MOBILE={"PALETTE": {"not-a-token": "#112233"}})
def test_unknown_palette_name_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="unknown"):
        get_config()


def test_readonly_requires_the_viewport_cookie() -> None:
    assert (
        readonly_blocks(
            cookie=None,
            model_label="library.tag",
            mixin_flag=True,
            configured_models=("library.book",),
        )
        is False
    )
    assert (
        readonly_blocks(
            cookie="mobile",
            model_label="library.book",
            mixin_flag=False,
            configured_models=("library.book",),
        )
        is True
    )
    assert (
        readonly_blocks(
            cookie="desktop",
            model_label="library.tag",
            mixin_flag=True,
            configured_models=(),
        )
        is False
    )


def test_query_is_collapsed_and_capped() -> None:
    assert clean_query("  a   b  ") == "a b"
    assert len(clean_query("x" * 200)) == 80
    assert clean_query(None) == ""


def test_search_hides_models_the_user_cannot_view(client: Client) -> None:
    author_model = get_user_model()
    admin = author_model.objects.create_superuser("root", "root@example.com", "secret")
    from library.models import Author

    writer = Author.objects.create(name="Ada Lovelace")
    Book.objects.create(title="Analytical Engine", author=writer, pages=12)
    client.force_login(admin)
    response = client.get(reverse("admin:admin_mobile_search"), {"q": "Analytical"})
    assert response.status_code == 200
    assert b"Analytical Engine" in response.content

    staff = author_model.objects.create_user(
        "clerk", "clerk@example.com", "secret", is_staff=True
    )
    client.force_login(staff)
    hidden = client.get(
        reverse("admin:admin_mobile_search"), {"q": "<script>Analytical"}
    )
    assert hidden.status_code == 200
    assert b"Analytical Engine" not in hidden.content
    assert b"&lt;script&gt;" in hidden.content


def test_anonymous_search_redirects(client: Client) -> None:
    response = client.get(reverse("admin:admin_mobile_search"), {"q": "Ada"})
    assert response.status_code == 302


def test_service_worker_is_static_only(client: Client) -> None:
    response = client.get(reverse("admin:admin_mobile_sw"))
    body = response.content.decode()
    assert response.status_code == 200
    assert response["Service-Worker-Allowed"] == "/admin/"
    assert "/static/" in body
    assert "text/html" not in body


def test_manifest_uses_sanitized_accent(client: Client) -> None:
    response = client.get(reverse("admin:admin_mobile_manifest"))
    payload = response.json()
    assert payload["display"] == "standalone"
    assert payload["theme_color"] == "#205067"
    assert payload["start_url"].endswith("/admin/")


def test_mobile_cookie_makes_tagged_model_readonly(client: Client) -> None:
    user_model = get_user_model()
    user = user_model.objects.create_superuser("root2", "root2@example.com", "secret")
    tag = Tag.objects.create(name="Paper", slug="paper")
    client.force_login(user)
    client.cookies["admin_mobile_viewport"] = "mobile"
    response = client.get(reverse("admin:library_tag_change", args=[tag.pk]))
    assert response.status_code == 200
    assert b'name="_save"' not in response.content


def test_features_stylesheet_has_no_hardcoded_colors() -> None:
    from pathlib import Path

    css = Path(
        "src/admin_mobile/static/admin_mobile/css/admin_mobile_features.css"
    ).read_text(encoding="utf-8")
    lowered = css.lower()
    assert 'html[data-theme="dark"]' in css or 'html[data-theme="dark"]' in css
    assert "prefers-color-scheme" in css
    assert "var(--body-bg)" in css
    for token in ("#fff", "#ffffff", "#000000", "rgb(", "rgba("):
        assert token not in lowered
