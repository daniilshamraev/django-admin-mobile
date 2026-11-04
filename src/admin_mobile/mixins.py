"""Per-model opt-in for native date and time widgets."""

from __future__ import annotations

from django.contrib.admin.sites import AdminSite
from django.db import models

from admin_mobile.overrides import (
    NATIVE_FORMFIELD_OVERRIDES,
    install_native_overrides,
)


class MobileAdminMixin:
    """Use native date widgets on one ``ModelAdmin`` or inline.

    List this mixin before ``admin.ModelAdmin`` (or ``TabularInline``).
    A custom ``formfield_overrides`` widget for a date field is left alone.
    The global ``USE_NATIVE_DATETIME`` flag is a separate opt-in.
    """

    formfield_overrides = {
        field_cls: dict(options)
        for field_cls, options in NATIVE_FORMFIELD_OVERRIDES.items()
    }

    def __init__(self, model: type[models.Model], admin_site: AdminSite) -> None:
        super().__init__(model, admin_site)
        install_native_overrides(self)
