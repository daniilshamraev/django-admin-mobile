from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "admin_mobile"
CSS = (PACKAGE / "static/admin_mobile/css/admin_mobile.css").read_text(encoding="utf-8")
JS = (PACKAGE / "static/admin_mobile/js/admin_mobile.js").read_text(encoding="utf-8")


def test_css_uses_admin_variables_and_theme_hooks() -> None:
    assert "var(--body-bg)" in CSS
    assert "var(--hairline-color)" in CSS
    assert 'html[data-theme="dark"]' in CSS
    assert 'html[data-theme="light"]' in CSS
    assert "prefers-color-scheme" in CSS
    assert "http://" not in CSS
    assert "https://" not in CSS
    assert "@import" not in CSS


def test_css_covers_each_toggle() -> None:
    assert "admin-mobile-cards" in CSS
    assert "max-width: 600px" in CSS
    assert "min-width: 601px" in CSS
    assert "overflow-x: auto" in CSS
    assert "attr(data-label)" in CSS
    assert "admin-mobile-inlines" in CSS
    assert ".empty-form" in CSS
    assert "position: sticky" in CSS
    assert "font-size: 16px" in CSS
    assert "min-height: 44px" in CSS
    assert "admin-mobile-filter-toggle" in CSS
    assert "#changelist-filter" in CSS


def test_css_covers_builtin_admin_surfaces() -> None:
    for selector in (
        "#header",
        "#user-tools",
        "#nav-sidebar",
        "#nav-filter",
        "#toggle-nav-sidebar",
        ".breadcrumbs",
        "body.login",
        "ul.messagelist",
        ".toplinks",
        ".admin-mobile-sort",
        ".admin-mobile-select-all",
        "#change-history",
        "table.model",
        ".errornote",
        ".related-widget-wrapper",
        ".related-lookup",
        ".select2-container",
        ".selector",
        "ul.radiolist",
        ".clearable-file-input",
        "data-inline-type",
        "body.delete-confirmation",
        "body.popup",
        ".calendarbox",
        ".clockbox",
        'html[dir="rtl"]',
    ):
        assert selector in CSS


def test_js_labels_rows_and_toggles_filters() -> None:
    assert "data-label" in JS
    assert "formset:added" in JS
    assert "changelist-filter" in JS
    assert "result_list" in JS
    assert "admin-mobile-select-all" in JS
    assert "admin-mobile-sort" in JS
    assert "change-history" in JS
    assert "javascript:" in JS
    assert "eval(" not in JS
    assert "new Function" not in JS
    assert "http://" not in JS
    assert "https://" not in JS
