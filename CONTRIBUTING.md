# Contributing

`django-admin-mobile` keeps the stock Django admin and only adds a stylesheet, a small script, and optional native date widgets.

## Setup

```bash
uv sync --extra dev
uv run python example/manage.py migrate
```

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -m "not playwright"
uv run pytest -m playwright
uv run tox
```

Playwright needs Chromium once: `uv run playwright install chromium`.

The screenshot test writes `docs/screenshots/*.png`. Update those files in the same change when the phone layout changes.

## Compatibility

The tox and GitHub Actions matrices cover Django 4.2, 5.2, and 6.0 on Python 3.10+ (Django 6 requires 3.12+). Do not add a build step or a CDN. Static files ship as plain CSS and JavaScript.

## Project layout

- `src/admin_mobile/` is the installable app.
- `example/` is a local admin with books, chapters, dates, and filters.
- `tests/` covers settings, widgets, template injection, and the phone screenshots.

Feature-Sliced Design is for product frontends. This repository stays a single Django app so `INSTALLED_APPS` can load it.
