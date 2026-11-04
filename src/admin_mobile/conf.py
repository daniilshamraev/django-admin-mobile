"""Typed view of the ``ADMIN_MOBILE`` setting."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from admin_mobile.colors import sanitize_hex

_BOOL_FIELDS: dict[str, str] = {
    "ENABLED": "enabled",
    "CHANGELIST_CARDS": "changelist_cards",
    "TABULAR_INLINE_STACK": "tabular_inline_stack",
    "STICKY_SUBMIT": "sticky_submit",
    "TOUCH_TARGETS": "touch_targets",
    "COLLAPSIBLE_FILTERS": "collapsible_filters",
    "USE_NATIVE_DATETIME": "use_native_datetime",
    "BOTTOM_TABS": "bottom_tabs",
    "GLOBAL_SEARCH": "global_search",
    "SWIPE_ACTIONS": "swipe_actions",
    "PULL_TO_REFRESH": "pull_to_refresh",
    "INFINITE_SCROLL": "infinite_scroll",
    "FILTER_SHEET": "filter_sheet",
    "STICKY_ACTIONS": "sticky_actions",
    "UNSAVED_GUARD": "unsaved_guard",
    "FORM_DRAFTS": "form_drafts",
    "CAMERA_CAPTURE": "camera_capture",
    "CAMERA_COMPRESS": "camera_compress",
    "MOBILE_KEYBOARDS": "mobile_keyboards",
    "FORM_NAVIGATOR": "form_navigator",
    "SHEET_PICKERS": "sheet_pickers",
    "PWA": "pwa",
    "HAPTICS": "haptics",
    "LIGHTBOX": "lightbox",
    "UNDO_DELETE": "undo_delete",
    "SWIPE_CONFIRM": "swipe_confirm",
    "DOUBLE_SUBMIT_GUARD": "double_submit_guard",
}

_VALUE_FIELDS = frozenset(
    {"ACCENT", "PALETTE", "UNDO_SECONDS", "READONLY_MODELS", "SWIPE_CONFIRM_ACTIONS"}
)
_MODEL_KEY = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_ACTION_KEY = re.compile(r"^[A-Za-z0-9_]{1,40}$")


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
    bottom_tabs: bool = True
    global_search: bool = True
    swipe_actions: bool = True
    pull_to_refresh: bool = True
    infinite_scroll: bool = False
    filter_sheet: bool = True
    sticky_actions: bool = True
    unsaved_guard: bool = True
    form_drafts: bool = False
    camera_capture: bool = True
    camera_compress: bool = True
    mobile_keyboards: bool = True
    form_navigator: bool = True
    sheet_pickers: bool = True
    pwa: bool = True
    haptics: bool = True
    lightbox: bool = True
    undo_delete: bool = False
    swipe_confirm: bool = True
    double_submit_guard: bool = True
    accent: str | None = None
    palette: tuple[tuple[str, str], ...] = ()
    undo_seconds: int = 8
    readonly_models: tuple[str, ...] = ()
    swipe_confirm_actions: tuple[str, ...] = ("delete_selected",)


def _bool_value(key: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ImproperlyConfigured(f"ADMIN_MOBILE[{key!r}] must be a bool.")
    return value


def _string_list(
    key: str, value: object, pattern: re.Pattern[str], limit: int
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or isinstance(value, str):
        raise ImproperlyConfigured(f"ADMIN_MOBILE[{key!r}] must be a list of strings.")
    if len(value) > limit:
        raise ImproperlyConfigured(f"ADMIN_MOBILE[{key!r}] has too many entries.")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or pattern.fullmatch(item) is None:
            raise ImproperlyConfigured(f"ADMIN_MOBILE[{key!r}] has an invalid entry.")
        items.append(item)
    return tuple(items)


def _palette(value: object) -> tuple[tuple[str, str], ...]:
    from admin_mobile.colors import PALETTE_PROPERTIES

    if not isinstance(value, Mapping):
        raise ImproperlyConfigured("ADMIN_MOBILE['PALETTE'] must be a dict.")
    pairs: list[tuple[str, str]] = []
    for name, color in value.items():
        if not isinstance(name, str) or name not in PALETTE_PROPERTIES:
            raise ImproperlyConfigured("ADMIN_MOBILE['PALETTE'] has an unknown name.")
        hex_color = sanitize_hex(color)
        if hex_color is None:
            raise ImproperlyConfigured("ADMIN_MOBILE['PALETTE'] colors must be hex.")
        pairs.append((name, hex_color))
    return tuple(pairs)


def get_config() -> AdminMobileSettings:
    """Read ``ADMIN_MOBILE`` on each call so ``override_settings`` works."""

    raw = getattr(settings, "ADMIN_MOBILE", None)
    if raw is None:
        return AdminMobileSettings()
    if not isinstance(raw, Mapping):
        raise ImproperlyConfigured("ADMIN_MOBILE must be a dict of booleans.")

    allowed = set(_BOOL_FIELDS) | _VALUE_FIELDS
    unknown = sorted(str(key) for key in raw if key not in allowed)
    if unknown:
        names = ", ".join(unknown)
        allowed_text = ", ".join(sorted(allowed))
        raise ImproperlyConfigured(
            f"Unknown ADMIN_MOBILE keys: {names}. Allowed keys: {allowed_text}."
        )

    values: dict[str, object] = {}
    for key, attr in _BOOL_FIELDS.items():
        if key in raw:
            values[attr] = _bool_value(key, raw[key])
    if "ACCENT" in raw:
        color = sanitize_hex(raw["ACCENT"])
        if color is None:
            raise ImproperlyConfigured("ADMIN_MOBILE['ACCENT'] must be a hex color.")
        values["accent"] = color
    if "PALETTE" in raw:
        values["palette"] = _palette(raw["PALETTE"])
    if "UNDO_SECONDS" in raw:
        seconds = raw["UNDO_SECONDS"]
        if (
            isinstance(seconds, bool)
            or not isinstance(seconds, int)
            or not 5 <= seconds <= 10
        ):
            raise ImproperlyConfigured(
                "ADMIN_MOBILE['UNDO_SECONDS'] must be an int from 5 to 10."
            )
        values["undo_seconds"] = seconds
    if "READONLY_MODELS" in raw:
        values["readonly_models"] = _string_list(
            "READONLY_MODELS", raw["READONLY_MODELS"], _MODEL_KEY, 100
        )
    if "SWIPE_CONFIRM_ACTIONS" in raw:
        values["swipe_confirm_actions"] = _string_list(
            "SWIPE_CONFIRM_ACTIONS", raw["SWIPE_CONFIRM_ACTIONS"], _ACTION_KEY, 20
        )
    return AdminMobileSettings(**values)
