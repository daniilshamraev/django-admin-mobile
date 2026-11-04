"""Attach mobile routes to the admin site without an extra URLconf entry."""

from __future__ import annotations

_PATCHED = False


def install_admin_routes() -> None:
    global _PATCHED
    if _PATCHED:
        return
    from django.contrib.admin.sites import AdminSite
    from django.urls import path

    original = AdminSite.get_urls

    def get_urls(self):
        from admin_mobile.views import (
            manifest,
            recent_view,
            search_view,
            service_worker,
        )

        extra = [
            path(
                "admin-mobile/search/",
                self.admin_view(search_view),
                name="admin_mobile_search",
            ),
            path(
                "admin-mobile/recent/",
                self.admin_view(recent_view),
                name="admin_mobile_recent",
            ),
            path("admin-mobile/sw.js", service_worker, name="admin_mobile_sw"),
            path(
                "admin-mobile/manifest.webmanifest",
                manifest,
                name="admin_mobile_manifest",
            ),
        ]
        return extra + original(self)

    AdminSite.get_urls = get_urls
    _PATCHED = True
