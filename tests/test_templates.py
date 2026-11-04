from pathlib import Path

import pytest
from django.template import Context, Template
from django.template.loader import get_template
from django.test import Client, override_settings
from django.urls import reverse

from admin_mobile.templatetags.admin_mobile import admin_mobile_assets


def test_base_template_extends_admin_and_calls_super() -> None:
    template = get_template("admin/base.html")
    origin = template.origin
    assert origin is not None
    assert "admin_mobile" in str(origin.name)
    source = Path(origin.name).read_text(encoding="utf-8")
    assert '{% extends "admin/base.html" %}' in source
    assert "{{ block.super }}" in source
    assert 'admin_mobile_assets "style"' in source
    assert 'admin_mobile_assets "script"' in source


def test_login_page_composes_with_django_admin(client: Client) -> None:
    response = client.get(reverse("admin:login"))
    html = response.content.decode()
    assert response.status_code == 200
    assert "admin/css/base.css" in html
    assert "admin/css/responsive.css" in html
    assert "admin_mobile/css/admin_mobile.css" in html
    assert "admin_mobile/js/admin_mobile.js" in html
    assert "admin-mobile-cards" in html
    assert "admin-mobile-inlines" in html
    assert "admin-mobile-sticky" in html
    assert "admin-mobile-touch" in html
    assert "admin-mobile-filters" in html


@override_settings(ADMIN_MOBILE={"ENABLED": False})
def test_disabled_package_emits_no_assets(client: Client) -> None:
    response = client.get(reverse("admin:login"))
    html = response.content.decode()
    assert "admin/css/base.css" in html
    assert "admin_mobile" not in html


@override_settings(ADMIN_MOBILE={"CHANGELIST_CARDS": False, "STICKY_SUBMIT": False})
def test_individual_flags_drop_classes() -> None:
    html = str(admin_mobile_assets("style"))
    assert "admin-mobile-cards" not in html
    assert "admin-mobile-sticky" not in html
    assert "admin-mobile-touch" in html
    assert "admin_mobile.css" in html


def test_script_kind_is_only_the_script() -> None:
    html = str(admin_mobile_assets("script"))
    assert html.startswith("<script ")
    assert "admin_mobile.js" in html
    assert "<link" not in html


def test_all_kind_includes_style_and_script() -> None:
    html = str(admin_mobile_assets())
    assert "admin_mobile.css" in html
    assert "admin_mobile.js" in html


def test_template_tag_loads() -> None:
    html = Template("{% load admin_mobile %}{% admin_mobile_assets %}").render(
        Context()
    )
    assert "admin_mobile.css" in html


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="kind"):
        admin_mobile_assets("stylesheet")


def test_filters_label_cannot_break_out_of_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "admin_mobile.templatetags.admin_mobile.gettext",
        lambda message: "</script><script>alert(1)</script>",
    )
    html = str(admin_mobile_assets("style"))
    assert "<script>alert" not in html
    assert "\\u003c/script\\u003e" in html


@override_settings(ADMIN_MOBILE={"ENABLED": False})
def test_tag_empty_when_disabled() -> None:
    assert str(admin_mobile_assets()) == ""
