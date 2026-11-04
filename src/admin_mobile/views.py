"""Admin-mounted pages: search, recent log, manifest, and the service worker."""

from __future__ import annotations

from django.contrib.admin.models import LogEntry
from django.contrib.admin.sites import site
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.cache import never_cache

from admin_mobile.colors import sanitize_hex
from admin_mobile.conf import get_config
from admin_mobile.search import clean_query, search_registered

_SW = """\
"use strict";
var CACHE = "admin-mobile-static-v1";
self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;
  var url;
  try { url = new URL(request.url); } catch (error) { return; }
  if (url.origin !== self.location.origin) return;
  if (url.pathname.indexOf("/static/") !== 0) return;
  event.respondWith(
    caches.open(CACHE).then(function (cache) {
      return fetch(request).then(function (response) {
        if (response && response.ok) cache.put(request, response.clone());
        return response;
      }).catch(function () {
        return cache.match(request);
      });
    })
  );
});
"""


def search_view(request: HttpRequest) -> HttpResponse:
    query = clean_query(request.GET.get("q", ""))
    hits = search_registered(request, query) if query else []
    return render(
        request,
        "admin/admin_mobile/search.html",
        {"query": query, "hits": hits, "title": "Search"},
    )


def recent_view(request: HttpRequest) -> HttpResponse:
    rows = []
    if request.user.is_active and request.user.is_staff:
        entries = LogEntry.objects.filter(user=request.user).select_related(
            "content_type"
        )[:20]
        for entry in entries:
            content_type = entry.content_type
            if content_type is None:
                continue
            model = content_type.model_class()
            if model is None or model not in site._registry:
                continue
            model_admin = site._registry[model]
            if not model_admin.has_view_permission(request):
                continue
            url = entry.get_admin_url()
            if not url:
                continue
            rows.append(
                {"label": entry.object_repr, "url": url, "when": entry.action_time}
            )
    return render(
        request,
        "admin/admin_mobile/recent.html",
        {"rows": rows, "title": "Recent"},
    )


@never_cache
def service_worker(_request: HttpRequest) -> HttpResponse:
    response = HttpResponse(_SW, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/admin/"
    response["Cache-Control"] = "no-cache"
    return response


@never_cache
def manifest(request: HttpRequest) -> JsonResponse:
    try:
        start = reverse("admin:index")
    except NoReverseMatch:
        start = "/admin/"
    payload: dict[str, object] = {
        "name": "Django admin",
        "short_name": "Admin",
        "start_url": start,
        "scope": "/admin/",
        "display": "standalone",
        "icons": [
            {
                "src": "/static/admin_mobile/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": "/static/admin_mobile/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
            },
        ],
    }
    header = sanitize_hex(request.COOKIES.get("admin_mobile_header", ""))
    accent = get_config().accent
    color = header or accent
    if color:
        payload["theme_color"] = color
        payload["background_color"] = color
    return JsonResponse(payload)
