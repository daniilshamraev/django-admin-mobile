# django-admin-mobile

Phone layout for the **native** Django admin. It is not a theme: colors, typography, and chrome stay on Django's own CSS variables, including `html[data-theme]` and `prefers-color-scheme`.

Targets Django 4.2 LTS, 5.x, and 6.x on Python 3.10+.

![Changelist at 375px](docs/screenshots/changelist-375.png)

![Change form at 375px](docs/screenshots/change-form-375.png)

## Install

```bash
pip install django-admin-mobile
```

Put the app **before** `django.contrib.admin`:

```python
INSTALLED_APPS = [
    "admin_mobile",
    "django.contrib.admin",
    # ...
]
```

That is enough. `admin_mobile` overrides `admin/base.html`, calls `{{ block.super }}`, and appends its CSS and JS inside `extrastyle` and `extrahead`. Projects that only override `admin/base_site.html` keep working, because that template still extends `admin/base.html`.

No CDN and no build step. The package ships plain files under `admin_mobile/static/`.

## If you already override `admin/base.html`

Django will use your template and skip this app's override. Load the tag yourself, and still call `{{ block.super }}`:

```django
{% extends "admin/base.html" %}
{% load admin_mobile %}

{% block extrastyle %}
{{ block.super }}
{% admin_mobile_assets "style" %}
{% endblock %}

{% block extrahead %}
{{ block.super }}
{% admin_mobile_assets "script" %}
{% endblock %}
```

`{% admin_mobile_assets %}` emits both. If `admin_mobile` is listed after `django.contrib.admin`, system check `admin_mobile.W001` warns you.

## Settings

All keys are optional booleans.

```python
ADMIN_MOBILE = {
    "ENABLED": True,
    "CHANGELIST_CARDS": True,
    "TABULAR_INLINE_STACK": True,
    "STICKY_SUBMIT": True,
    "TOUCH_TARGETS": True,
    "COLLAPSIBLE_FILTERS": True,
    "USE_NATIVE_DATETIME": False,
}
```

| Key | Default | Effect |
| --- | --- | --- |
| `ENABLED` | `True` | Turn the stylesheet and script off. |
| `CHANGELIST_CARDS` | `True` | At `≤600px`, changelist rows become cards. `data-label` is copied from the column header. From 601px to 1024px the table scrolls sideways instead. Checkboxes and links stay in the row. |
| `TABULAR_INLINE_STACK` | `True` | Tabular inlines stack into labeled fields. The empty template row stays hidden, so Django's `inlines.js` can still add and delete rows. |
| `STICKY_SUBMIT` | `True` | The last `.submit-row` sticks to the bottom of the viewport. The login page is left alone. |
| `TOUCH_TARGETS` | `True` | Targets at least 44px, inputs at 16px (stops iOS from zooming), larger checkboxes. |
| `COLLAPSIBLE_FILTERS` | `True` | `#changelist-filter` collapses behind a button. Django's filters, django-admin-rangefilter, and django-more-admin-filters render inside that node; this package does not import them. |
| `USE_NATIVE_DATETIME` | `False` | Opt in to native date/time widgets on **every** `ModelAdmin` and inline. A custom `formfield_overrides` widget is kept. |

Unknown keys and non-booleans raise `ImproperlyConfigured`.

## Native date and time widgets

Per model, without the global flag:

```python
from django.contrib import admin
from admin_mobile.mixins import MobileAdminMixin
from library.models import Book


@admin.register(Book)
class BookAdmin(MobileAdminMixin, admin.ModelAdmin):
    pass
```

`MobileAdminMixin` must come before `admin.ModelAdmin` or `admin.TabularInline`. It sets `formfield_overrides` to:

- `admin_mobile.widgets.NativeDateInput` (`<input type="date">`)
- `admin_mobile.widgets.NativeTimeInput` (`<input type="time" step="1">`)
- `admin_mobile.widgets.NativeSplitDateTimeWidget`

Values stay on `SplitDateTimeField` / `DateField` / `TimeField`, so Django still validates them and still applies the current time zone. The widget renders the active zone (not the raw UTC instant) and prints that zone name under the inputs. ISO formats are required (`YYYY-MM-DD`, `HH:MM` or `HH:MM:SS`); a locale string such as `15.06.2024` is rejected. Microseconds are dropped, matching Django's admin split widget.

These widgets do **not** load `DateTimeShortcuts`, so you do not get a second calendar on top of the native picker.

## Example

```bash
uv sync --extra dev
uv run python example/manage.py migrate
uv run python example/manage.py runserver 127.0.0.1:8741
```

With `DEBUG` and `ADMIN_MOBILE_DEMO` (both set in `example/example/settings.py`) migrate creates a local superuser `admin` / `admin` and a few books. That password exists only for this demo. Do not set `ADMIN_MOBILE_DEMO` on a shared host; the seed refuses to run when `DEBUG` is off.

Open http://127.0.0.1:8741/admin/ and narrow the window to 375px, or use device mode.

![Filters open](docs/screenshots/filters-375.png)

![Changelist, dark](docs/screenshots/changelist-375-dark.png)

The same stylesheet also covers the rest of the built-in admin at `≤600px`: login, password change, and logout; the index and app list; the nav sidebar and its filter; header, user tools, and breadcrumbs; changelist search, actions, select-all, sortable headers, date hierarchy, pagination, result counts, and `list_editable`; every built-in filter (choices, related, date, empty, and facets on Django 5+); change-form fieldsets (including collapse), help, errors, readonly fields, related-object icons, raw id lookup, autocomplete, filter horizontal/vertical, radios, and file Currently/Change/Clear; stacked and tabular inlines; object history; delete confirmation; related-object popups; messages; the stock calendar and clock when native widgets are off; admindocs; and RTL (`dir="rtl"`, logical alignment).

Further 375px captures live in `docs/screenshots/` (`login`, `index`, `nav-sidebar`, `edition`, `calendar`, `clock`, `history`, `delete-confirm`, `popup`, `admindocs`, `rtl-changelist`, and others).

`Appointment` in the example keeps Django's calendar and clock. `Book` and `Edition` use `MobileAdminMixin`. `USE_NATIVE_DATETIME` stays off in the example so both modes are visible.

## Tests

```bash
uv run ruff check .
uv run pytest -m "not playwright"
uv run playwright install chromium
uv run pytest -m playwright
uv run tox
```

`tox.ini` runs Django 4.2, 5.2, and 6.0. GitHub Actions adds Python 3.10–3.13 where each Django release allows it.

## Publishing

The package is not on PyPI yet.

1. Create a GitHub repository and push this project.
2. Add `[project.urls]` in `pyproject.toml` (`Homepage`, `Repository`, `Changelog`).
3. Build: `uv build` (hatchling, src layout, static files and templates included).
4. Publish: `uv publish` with a PyPI API token. The name `django-admin-mobile` has to be free on PyPI; the import name is `admin_mobile`.

Author: Daniil Shamraev. License: MIT.
