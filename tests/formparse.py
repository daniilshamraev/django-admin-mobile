"""Pull posted admin fields out of a rendered change form."""

from __future__ import annotations

from html.parser import HTMLParser


class _AdminFormParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.fields: dict[str, str] = {}
        self._select_name: str | None = None
        self._selected: str | None = None
        self._saw_option = False
        self._textarea_name: str | None = None
        self._textarea_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: (item if item is not None else "") for key, item in attrs}
        if tag == "input":
            name = values.get("name", "")
            if not name or values.get("type") in {"submit", "button", "image"}:
                return
            if values.get("type") in {"checkbox", "radio"} and "checked" not in values:
                return
            self.fields[name] = values.get("value", "")
            return
        if tag == "select":
            self._select_name = values.get("name") or None
            self._selected = None
            self._saw_option = False
            return
        if tag == "option" and self._select_name:
            self._saw_option = True
            option_value = values.get("value", "")
            if "selected" in values or self._selected is None:
                self._selected = option_value
            return
        if tag == "textarea":
            self._textarea_name = values.get("name") or None
            self._textarea_parts = []

    def handle_data(self, data: str) -> None:
        if self._textarea_name is not None:
            self._textarea_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "select" and self._select_name and self._saw_option:
            self.fields[self._select_name] = self._selected or ""
            self._select_name = None
            return
        if tag == "textarea" and self._textarea_name:
            self.fields[self._textarea_name] = "".join(self._textarea_parts)
            self._textarea_name = None


def admin_form_data(html: str) -> dict[str, str]:
    parser = _AdminFormParser()
    parser.feed(html)
    return parser.fields
