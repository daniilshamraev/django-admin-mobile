"""Sanitize accent colors before they are written into a style tag."""

from __future__ import annotations

import re

_HEX = re.compile(r"^#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")

# Names map to Django admin custom properties. Unknown names are dropped.
PALETTE_PROPERTIES: dict[str, str] = {
    "accent": "--accent",
    "primary": "--primary",
    "secondary": "--secondary",
    "header-bg": "--header-bg",
    "header-link": "--header-link-color",
    "link-fg": "--link-fg",
    "button-bg": "--button-bg",
    "button-fg": "--button-fg",
    "default-button-bg": "--default-button-bg",
    "object-tools-bg": "--object-tools-bg",
    "body-bg": "--body-bg",
    "body-fg": "--body-fg",
    "hairline-color": "--hairline-color",
    "border-color": "--border-color",
}


def sanitize_hex(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if _HEX.fullmatch(text) is None:
        return None
    return text.lower()


def accent_declarations(
    accent: str | None, palette: tuple[tuple[str, str], ...]
) -> str:
    """CSS custom properties for the accent. Empty when nothing is configured."""

    props: dict[str, str] = {}
    if accent:
        # Interactive colors only. Header and body stay on the active theme.
        props["--accent"] = accent
        props["--button-bg"] = accent
        props["--default-button-bg"] = accent
        props["--object-tools-bg"] = accent
    for name, color in palette:
        css_name = PALETTE_PROPERTIES.get(name)
        if css_name and sanitize_hex(color):
            props[css_name] = color
    if not props:
        return ""
    body = "".join(f"{name}:{value};" for name, value in props.items())
    both = (
        "html.admin-mobile,"
        "html[data-theme='light'].admin-mobile,"
        "html[data-theme='dark'].admin-mobile,"
        "html[data-theme='auto'].admin-mobile"
    )
    auto = "html[data-theme='auto'].admin-mobile"
    return (
        f"{both}{{{body}}}"
        "@media (prefers-color-scheme: dark){"
        f"{auto}{{{body}}}}}"
    )
