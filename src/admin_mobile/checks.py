"""Install-order check. The template tag remains valid either way."""

from __future__ import annotations

from collections.abc import Sequence

from django.core.checks import Warning, register

_REGISTERED = False


def _is_admin_mobile(entry: str) -> bool:
    return entry == "admin_mobile" or entry.endswith(
        "admin_mobile.apps.AdminMobileConfig"
    )


def _is_django_admin(entry: str) -> bool:
    return entry in {
        "django.contrib.admin",
        "django.contrib.admin.apps.AdminConfig",
    }


def app_order_warnings(installed_apps: Sequence[str]) -> list[Warning]:
    mobile_at = next(
        (
            index
            for index, entry in enumerate(installed_apps)
            if _is_admin_mobile(entry)
        ),
        None,
    )
    admin_at = next(
        (
            index
            for index, entry in enumerate(installed_apps)
            if _is_django_admin(entry)
        ),
        None,
    )
    if mobile_at is None or admin_at is None or mobile_at < admin_at:
        return []
    return [
        Warning(
            "admin_mobile is listed after django.contrib.admin, so its "
            "admin/base.html override will not be selected.",
            hint=(
                "Put 'admin_mobile' before 'django.contrib.admin' in "
                "INSTALLED_APPS, or load {% admin_mobile_assets %} from your "
                "own admin/base.html."
            ),
            id="admin_mobile.W001",
        )
    ]


def check_installed_before_admin(
    app_configs: object,
    **kwargs: object,
) -> list[Warning]:
    from django.conf import settings

    return app_order_warnings(tuple(settings.INSTALLED_APPS))


def register_checks() -> None:
    global _REGISTERED
    if _REGISTERED:
        return
    register(check_installed_before_admin)
    _REGISTERED = True
