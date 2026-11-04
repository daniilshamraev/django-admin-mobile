"""Swap stock admin date widgets without touching a custom widget choice."""

from __future__ import annotations

from django import forms
from django.contrib.admin import widgets as admin_widgets
from django.contrib.admin.options import BaseModelAdmin
from django.db import models

from admin_mobile.conf import get_config
from admin_mobile.widgets import (
    ISO_DATE_INPUT_FORMATS,
    ISO_TIME_INPUT_FORMATS,
    NativeDateInput,
    NativeSplitDateTimeWidget,
    NativeTimeInput,
)

STOCK_WIDGETS: frozenset[type[forms.Widget]] = frozenset(
    {
        admin_widgets.AdminDateWidget,
        admin_widgets.AdminTimeWidget,
        admin_widgets.AdminSplitDateTime,
        admin_widgets.BaseAdminDateWidget,
        admin_widgets.BaseAdminTimeWidget,
    }
)

NATIVE_WIDGETS: frozenset[type[forms.Widget]] = frozenset(
    {
        NativeDateInput,
        NativeTimeInput,
        NativeSplitDateTimeWidget,
    }
)

NATIVE_FORMFIELD_OVERRIDES: dict[type[models.Field], dict[str, object]] = {
    models.DateField: {
        "widget": NativeDateInput,
        "input_formats": list(ISO_DATE_INPUT_FORMATS),
        "localize": False,
    },
    models.TimeField: {
        "widget": NativeTimeInput,
        "input_formats": list(ISO_TIME_INPUT_FORMATS),
        "localize": False,
    },
    models.DateTimeField: {
        "form_class": forms.SplitDateTimeField,
        "widget": NativeSplitDateTimeWidget,
        "input_date_formats": list(ISO_DATE_INPUT_FORMATS),
        "input_time_formats": list(ISO_TIME_INPUT_FORMATS),
        "localize": False,
    },
}

_PATCHED = False
_ORIGINAL_FORMFIELD = BaseModelAdmin.formfield_for_dbfield


def _native_spec(db_field: models.Field) -> dict[str, object] | None:
    for field_cls, spec in NATIVE_FORMFIELD_OVERRIDES.items():
        if isinstance(db_field, field_cls):
            return spec
    return None


def _current_widget(admin: BaseModelAdmin, db_field: models.Field) -> object | None:
    overrides = getattr(admin, "formfield_overrides", {})
    for klass in db_field.__class__.mro():
        options = overrides.get(klass)
        if isinstance(options, dict) and "widget" in options:
            return options["widget"]
    return None


def _is_replaceable(widget: object) -> bool:
    if widget is None:
        return True
    return widget in STOCK_WIDGETS or widget in NATIVE_WIDGETS


def install_native_overrides(admin: BaseModelAdmin) -> None:
    """Point stock date widgets at the native ones. Keep any other widget."""

    overrides: dict[type[models.Field], dict[str, object]] = {
        field_cls: dict(options)
        for field_cls, options in admin.formfield_overrides.items()
        if isinstance(options, dict)
    }
    for field_cls, spec in NATIVE_FORMFIELD_OVERRIDES.items():
        current = dict(overrides.get(field_cls, {}))
        if not _is_replaceable(current.get("widget")):
            continue
        current.update(spec)
        overrides[field_cls] = current
    admin.formfield_overrides = overrides


def apply_native_datetime(
    admin: BaseModelAdmin,
    db_field: models.Field,
    kwargs: dict[str, object],
) -> None:
    """Fill native widget kwargs when the admin is still on the stock widget.

    ``formfield_for_dbfield`` merges ``formfield_overrides`` under ``kwargs``,
    so values placed here win over ``AdminDateWidget`` and lose to an explicit
    widget argument from a caller.
    """

    if db_field.choices:
        return
    spec = _native_spec(db_field)
    if spec is None or not _is_replaceable(_current_widget(admin, db_field)):
        return
    for key, value in spec.items():
        kwargs.setdefault(key, value)


def install_native_datetime_patch() -> None:
    """Wrap ``BaseModelAdmin.formfield_for_dbfield`` once.

    The wrapper checks the setting on every call so tests can toggle it.
    Inlines inherit ``BaseModelAdmin``, not ``ModelAdmin``, so the patch has
    to sit on the shared base.
    """

    global _PATCHED
    if _PATCHED:
        return

    def formfield_for_dbfield(
        self: BaseModelAdmin,
        db_field: models.Field,
        request: object,
        **kwargs: object,
    ) -> forms.Field | None:
        if get_config().use_native_datetime:
            apply_native_datetime(self, db_field, kwargs)
        return _ORIGINAL_FORMFIELD(self, db_field, request, **kwargs)

    BaseModelAdmin.formfield_for_dbfield = formfield_for_dbfield
    _PATCHED = True
