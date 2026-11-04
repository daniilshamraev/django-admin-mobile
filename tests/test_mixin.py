import pytest
from django import forms
from django.contrib import admin
from django.contrib.admin import widgets as admin_widgets
from django.db import models
from django.test import RequestFactory, override_settings

from admin_mobile.mixins import MobileAdminMixin
from admin_mobile.overrides import install_native_datetime_patch
from admin_mobile.widgets import (
    NativeDateInput,
    NativeSplitDateTimeWidget,
    NativeTimeInput,
)
from library.admin import AppointmentAdmin, BookAdmin, ChapterInline
from library.models import Appointment, Author, Book, Chapter

pytestmark = pytest.mark.django_db


class _CustomDateInput(forms.DateInput):
    pass


class _PlainBookAdmin(admin.ModelAdmin):
    pass


class _CustomBookAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateField: {"widget": _CustomDateInput},
    }


class _MixinCustomBookAdmin(MobileAdminMixin, admin.ModelAdmin):
    formfield_overrides = {
        models.DateField: {"widget": _CustomDateInput},
    }


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


def test_patch_is_idempotent() -> None:
    install_native_datetime_patch()
    install_native_datetime_patch()


def test_mixin_uses_native_widgets(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    model_admin = BookAdmin(Book, admin.site)
    published = model_admin.formfield_for_dbfield(
        Book._meta.get_field("published_on"),
        request,
    )
    reading = model_admin.formfield_for_dbfield(
        Book._meta.get_field("reading_time"),
        request,
    )
    scheduled = model_admin.formfield_for_dbfield(
        Book._meta.get_field("scheduled_for"),
        request,
    )
    title = model_admin.formfield_for_dbfield(Book._meta.get_field("title"), request)
    assert published is not None and isinstance(published.widget, NativeDateInput)
    assert published.localize is False
    assert reading is not None and isinstance(reading.widget, NativeTimeInput)
    assert scheduled is not None and isinstance(
        scheduled.widget, NativeSplitDateTimeWidget
    )
    assert title is not None
    assert isinstance(title.widget, admin_widgets.AdminTextInputWidget)


def test_inline_mixin_uses_native_time(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    inline = ChapterInline(Book, admin.site)
    field = inline.formfield_for_dbfield(Chapter._meta.get_field("starts_at"), request)
    assert field is not None
    assert isinstance(field.widget, NativeTimeInput)


def test_appointment_keeps_stock_calendar_widget(
    request_factory: RequestFactory,
) -> None:
    request = request_factory.get("/admin/")
    model_admin = AppointmentAdmin(Appointment, admin.site)
    field = model_admin.formfield_for_dbfield(
        Appointment._meta.get_field("on_date"),
        request,
    )
    assert field is not None
    assert isinstance(field.widget, admin_widgets.AdminDateWidget)


def test_global_off_keeps_stock_widget(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    model_admin = _PlainBookAdmin(Author, admin.site)
    field = model_admin.formfield_for_dbfield(
        Author._meta.get_field("birth_date"),
        request,
    )
    assert field is not None
    assert isinstance(field.widget, admin_widgets.AdminDateWidget)


@override_settings(ADMIN_MOBILE={"USE_NATIVE_DATETIME": True})
def test_global_opt_in_replaces_stock_widget(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    model_admin = _PlainBookAdmin(Author, admin.site)
    field = model_admin.formfield_for_dbfield(
        Author._meta.get_field("birth_date"),
        request,
    )
    assert field is not None
    assert isinstance(field.widget, NativeDateInput)
    assert field.localize is False


@override_settings(ADMIN_MOBILE={"USE_NATIVE_DATETIME": True})
def test_global_opt_in_keeps_custom_widget(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    model_admin = _CustomBookAdmin(Author, admin.site)
    field = model_admin.formfield_for_dbfield(
        Author._meta.get_field("birth_date"),
        request,
    )
    assert field is not None
    assert isinstance(field.widget, _CustomDateInput)


def test_mixin_keeps_custom_date_widget(request_factory: RequestFactory) -> None:
    request = request_factory.get("/admin/")
    model_admin = _MixinCustomBookAdmin(Author, admin.site)
    field = model_admin.formfield_for_dbfield(
        Author._meta.get_field("birth_date"),
        request,
    )
    assert field is not None
    assert isinstance(field.widget, _CustomDateInput)


@override_settings(ADMIN_MOBILE={"USE_NATIVE_DATETIME": True})
def test_choice_field_is_not_forced_to_native_date(
    request_factory: RequestFactory,
) -> None:
    request = request_factory.get("/admin/")
    model_admin = _PlainBookAdmin(Book, admin.site)
    field = model_admin.formfield_for_dbfield(Book._meta.get_field("status"), request)
    assert field is not None
    assert not isinstance(field.widget, NativeDateInput)
