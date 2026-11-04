"""Asset tag used by the bundled ``admin/base.html`` and by custom bases."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from django import template
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext

from admin_mobile.colors import accent_declarations
from admin_mobile.conf import AdminMobileSettings, get_config
from admin_mobile.history import history_count, history_groups

register = template.Library()

_CLASS_BY_FLAG: tuple[tuple[str, str], ...] = (
    ("changelist_cards", "admin-mobile-cards"),
    ("tabular_inline_stack", "admin-mobile-inlines"),
    ("sticky_submit", "admin-mobile-sticky"),
    ("touch_targets", "admin-mobile-touch"),
    ("collapsible_filters", "admin-mobile-filters"),
    ("bottom_tabs", "admin-mobile-tabs"),
    ("filter_sheet", "admin-mobile-filter-sheet"),
    ("sticky_actions", "admin-mobile-bulk"),
    ("haptics", "admin-mobile-haptics"),
    ("form_navigator", "admin-mobile-formnav"),
    ("lightbox", "admin-mobile-lightbox"),
    ("pwa", "admin-mobile-pwa"),
    ("infinite_scroll", "admin-mobile-infinite"),
    ("pull_to_refresh", "admin-mobile-pull"),
)
_FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_KINDS = frozenset({"all", "style", "script"})


def _js_string(value: str) -> str:
    """JSON string literal safe to drop into an HTML script block."""

    encoded = json.dumps(value, ensure_ascii=True)
    return (
        encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )


def _class_script(config: AdminMobileSettings) -> SafeString:
    classes = ["admin-mobile"]
    classes.extend(
        css_class for attr, css_class in _CLASS_BY_FLAG if getattr(config, attr) is True
    )
    adds = "".join(
        f"root.classList.add({_js_string(css_class)});" for css_class in classes
    )
    filters_label = _js_string(gettext("Filters"))
    select_label = _js_string(gettext("Select"))
    sort_label = _js_string(gettext("Sort by"))
    # Class names and labels are fixed strings or gettext output passed through
    # _js_string. mark_safe is limited to that script.
    script = (
        "<script>(function(){var root=document.documentElement;"
        f"{adds}"
        f"root.setAttribute('data-admin-mobile-filters-label',{filters_label});"
        f"root.setAttribute('data-admin-mobile-select-label',{select_label});"
        f"root.setAttribute('data-admin-mobile-sort-label',{sort_label});"
        "})();</script>"
    )
    return mark_safe(script)


def _json_blob(element_id: str, payload: dict[str, object]) -> SafeString:
    raw = json.dumps(payload, ensure_ascii=True).replace("<", "\\u003c")
    return mark_safe(
        f'<script type="application/json" id="{element_id}">{raw}</script>'
    )


def _reverse(name: str) -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return ""


def _feature_config(config: AdminMobileSettings) -> SafeString:
    payload: dict[str, object] = {
        "searchUrl": _reverse("admin:admin_mobile_search")
        if config.global_search
        else "",
        "recentUrl": _reverse("admin:admin_mobile_recent"),
        "swUrl": _reverse("admin:admin_mobile_sw") if config.pwa else "",
        "manifestUrl": _reverse("admin:admin_mobile_manifest") if config.pwa else "",
        "infiniteScroll": config.infinite_scroll,
        "pullToRefresh": config.pull_to_refresh,
        "swipe": config.swipe_actions,
        "drafts": config.form_drafts,
        "unsaved": config.unsaved_guard,
        "camera": config.camera_capture,
        "compress": config.camera_compress,
        "keyboards": config.mobile_keyboards,
        "pickers": config.sheet_pickers,
        "haptics": config.haptics,
        "lightbox": config.lightbox,
        "undoDelete": config.undo_delete,
        "undoSeconds": config.undo_seconds,
        "swipeConfirm": config.swipe_confirm,
        "swipeConfirmActions": list(config.swipe_confirm_actions),
        "doubleSubmit": config.double_submit_guard,
        "tabs": config.bottom_tabs,
        "bulk": config.sticky_actions,
        "filterSheet": config.filter_sheet,
        "navigator": config.form_navigator,
        "pwa": config.pwa,
    }
    return _json_blob("admin-mobile-config", payload)


def _style(config: AdminMobileSettings) -> SafeString:
    href = static("admin_mobile/css/admin_mobile.css")
    # CSS hides the filter before JS runs. Without JS, show it again.
    noscript = mark_safe(
        "<noscript><style>"
        "@media (max-width:600px){"
        "html.admin-mobile-filters #changelist-filter{display:block !important}"
        "}"
        "</style></noscript>"
    )
    link = format_html('<link rel="stylesheet" href="{}">', href)
    features_href = static("admin_mobile/css/admin_mobile_features.css")
    features_link = format_html('<link rel="stylesheet" href="{}">', features_href)
    accent = accent_declarations(config.accent, config.palette)
    accent_tag = (
        mark_safe(f'<style id="admin-mobile-accent">{accent}</style>')
        if accent
        else mark_safe("")
    )
    return mark_safe(
        f"{_class_script(config)}{_feature_config(config)}{link}{features_link}{accent_tag}{noscript}"
    )


def _script() -> SafeString:
    src = static("admin_mobile/js/admin_mobile.js")
    features = static("admin_mobile/js/admin_mobile_features.js")
    return format_html(
        '<script src="{}" defer id="admin-mobile-script"></script>'
        '<script src="{}" defer id="admin-mobile-features"></script>',
        src,
        features,
    )


def _safe_field(value: object) -> str:
    if isinstance(value, str) and _FIELD_NAME.fullmatch(value):
        return value
    return ""


@register.simple_tag
def admin_mobile_history_groups(
    action_list: Iterable[object],
) -> list[dict[str, object]]:
    """Log rows grouped by day, newest first, for the phone timeline."""

    return history_groups(action_list)


@register.simple_tag
def admin_mobile_history_count(action_list: Iterable[object]) -> int:
    return history_count(action_list)


@register.simple_tag
def admin_mobile_card_config(cl: object) -> SafeString:
    """JSON describing which changelist columns become the phone card."""

    model_admin = getattr(cl, "model_admin", None)
    if model_admin is None:
        return mark_safe("")
    fields = getattr(model_admin, "mobile_list_display", None) or ()
    payload: dict[str, object] = {
        "title": _safe_field(getattr(model_admin, "mobile_card_title", None)),
        "subtitle": _safe_field(getattr(model_admin, "mobile_card_subtitle", None)),
        "image": _safe_field(getattr(model_admin, "mobile_card_image", None)),
        "fields": [name for item in fields if (name := _safe_field(item))],
    }
    return _json_blob("admin-mobile-card-config", payload)


@register.simple_tag
def admin_mobile_assets(kind: str = "all") -> SafeString:
    """Emit the stylesheet, the script, or both.

    ``kind`` is ``"style"`` (``extrastyle``), ``"script"`` (``extrahead``),
    or ``"all"``. Output is empty when ``ADMIN_MOBILE['ENABLED']`` is false.
    """

    if kind not in _KINDS:
        allowed = ", ".join(sorted(_KINDS))
        raise ValueError(f"admin_mobile_assets kind must be one of: {allowed}.")
    config = get_config()
    if not config.enabled:
        return mark_safe("")
    style = _style(config)
    script = _script()
    if kind == "style":
        return style
    if kind == "script":
        return script
    return mark_safe(f"{style}{script}")
