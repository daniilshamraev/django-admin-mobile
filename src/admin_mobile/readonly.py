"""UX-only read-only mode. A cookie is not an authorization boundary."""

from __future__ import annotations

from django.contrib.admin.options import BaseModelAdmin
from django.http import HttpRequest

from admin_mobile.conf import get_config

_PATCHED = False
VIEWPORT_COOKIE = "admin_mobile_viewport"
MOBILE_VALUE = "mobile"


def model_key(model: type) -> str:
    meta = model._meta
    return f"{meta.app_label}.{meta.model_name}"


def readonly_blocks(
    *,
    cookie: str | None,
    model_label: str,
    mixin_flag: bool,
    configured_models: tuple[str, ...],
) -> bool:
    """True when this request should hide add/change/delete.

    The viewport cookie is set by our script. Desktop clients, curl, and a
    removed cookie keep full permissions. This is a layout guard, not security.
    """

    if cookie != MOBILE_VALUE:
        return False
    if mixin_flag:
        return True
    return model_label in configured_models


def _blocks_admin(admin: BaseModelAdmin, request: HttpRequest | None) -> bool:
    if not get_config().enabled or request is None:
        return False
    model = getattr(admin, "model", None)
    if model is None:
        return False
    return readonly_blocks(
        cookie=request.COOKIES.get(VIEWPORT_COOKIE),
        model_label=model_key(model),
        mixin_flag=bool(getattr(admin, "mobile_readonly", False)),
        configured_models=get_config().readonly_models,
    )


def install_readonly_guard() -> None:
    global _PATCHED
    if _PATCHED:
        return
    from django.contrib.admin.options import ModelAdmin

    def _wrap(original):
        def wrapped(self, request, *args, **kwargs):
            if _blocks_admin(self, request):
                return False
            return original(self, request, *args, **kwargs)

        return wrapped

    ModelAdmin.has_add_permission = _wrap(ModelAdmin.has_add_permission)
    ModelAdmin.has_change_permission = _wrap(ModelAdmin.has_change_permission)
    ModelAdmin.has_delete_permission = _wrap(ModelAdmin.has_delete_permission)
    _PATCHED = True
