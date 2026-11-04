from django.core.checks import run_checks

from admin_mobile.checks import app_order_warnings


def test_order_before_admin_is_quiet() -> None:
    warnings = app_order_warnings(["admin_mobile", "django.contrib.admin", "library"])
    assert warnings == []


def test_appconfig_path_before_admin_is_quiet() -> None:
    warnings = app_order_warnings(
        [
            "admin_mobile.apps.AdminMobileConfig",
            "django.contrib.admin.apps.AdminConfig",
        ]
    )
    assert warnings == []


def test_order_after_admin_warns() -> None:
    warnings = app_order_warnings(["django.contrib.admin", "admin_mobile"])
    assert len(warnings) == 1
    assert warnings[0].id == "admin_mobile.W001"


def test_missing_admin_does_not_warn() -> None:
    assert app_order_warnings(["admin_mobile"]) == []


def test_installed_project_passes_check() -> None:
    issues = [issue for issue in run_checks() if issue.id == "admin_mobile.W001"]
    assert issues == []
