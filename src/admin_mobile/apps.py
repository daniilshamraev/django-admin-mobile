from __future__ import annotations

from django.apps import AppConfig


class AdminMobileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_mobile"
    verbose_name = "Admin mobile"

    def ready(self) -> None:
        from admin_mobile.checks import register_checks
        from admin_mobile.overrides import install_native_datetime_patch

        register_checks()
        install_native_datetime_patch()
