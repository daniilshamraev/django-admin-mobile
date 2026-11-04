"""Typed view of the ``ADMIN_MOBILE`` setting."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_SETTING_TO_FIELD: dict[str, str] = {
    "ENABLED": "enabled",
    "CHANGELIST_CARDS": "changelist_cards",
    "TABULAR_INLINE_STACK": "tabular_inline_stack",
    "STICKY_SUBMIT": "sticky_submit",
    "TOUCH_TARGETS": "touch_targets",
    "COLLAPSIBLE_FILTERS": "collapsible_filters",
    "USE_NATIVE_DATETIME": "use_native_datetime",
}


@dataclass(frozen=True)
class AdminMobileSettings:
    """Feature flags. Missing keys keep these defaults."""

    enabled: bool = True
    changelist_cards: bool = True
    tabular_inline_stack: bool = True
    sticky_submit: bool = True
    touch_targets: bool = True
    collapsible_filters: bool = True
    use_native_datetime: bool = False


def get_config() -> AdminMobileSettings:
    """Read ``ADMIN_MOBILE`` on each call so ``override_settings`` works."""

    raw = getattr(settings, "ADMIN_MOBILE", None)
    if raw is None:
        return AdminMobileSettings()
    if not isinstance(raw, Mapping):
        raise ImproperlyConfigured("ADMIN_MOBILE must be a dict of booleans.")

    unknown = sorted(str(key) for key in raw if key not in _SETTING_TO_FIELD)
    if unknown:
        names = ", ".join(unknown)
        allowed = ", ".join(sorted(_SETTING_TO_FIELD))
        raise ImproperlyConfigured(
            f"Unknown ADMIN_MOBILE keys: {names}. Allowed keys: {allowed}."
        )

    values: dict[str, bool] = {}
    for key, attr in _SETTING_TO_FIELD.items():
        if key not in raw:
            continue
        value = raw[key]
        if not isinstance(value, bool):
            raise ImproperlyConfigured(f"ADMIN_MOBILE[{key!r}] must be a bool.")
        values[attr] = value
    return AdminMobileSettings(**values)
