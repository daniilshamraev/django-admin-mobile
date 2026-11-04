"""Asset tag used by the bundled ``admin/base.html`` and by custom bases."""

from __future__ import annotations

import json

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext

from admin_mobile.conf import AdminMobileSettings, get_config

register = template.Library()

_CLASS_BY_FLAG: tuple[tuple[str, str], ...] = (
    ("changelist_cards", "admin-mobile-cards"),
    ("tabular_inline_stack", "admin-mobile-inlines"),
    ("sticky_submit", "admin-mobile-sticky"),
    ("touch_targets", "admin-mobile-touch"),
    ("collapsible_filters", "admin-mobile-filters"),
)

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
    # Class names and labels are fixed strings or gettext output passed through
    # _js_string. mark_safe is limited to that script.
    script = (
        "<script>(function(){var root=document.documentElement;"
        f"{adds}"
        f"root.setAttribute('data-admin-mobile-filters-label',{filters_label});"
        f"root.setAttribute('data-admin-mobile-select-label',{select_label});"
        "})();</script>"
    )
    return mark_safe(script)


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
    return mark_safe(f"{_class_script(config)}{link}{noscript}")


def _script() -> SafeString:
    src = static("admin_mobile/js/admin_mobile.js")
    return format_html(
        '<script src="{}" defer id="admin-mobile-script"></script>',
        src,
    )


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
