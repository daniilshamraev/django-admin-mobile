"""Staff-only search across registered model admins."""

from __future__ import annotations

from dataclasses import dataclass

from django.contrib.admin.sites import site
from django.http import HttpRequest
from django.urls import NoReverseMatch, reverse

_MAX_QUERY = 80
_PER_MODEL = 5
_MAX_HITS = 20


@dataclass(frozen=True)
class SearchHit:
    label: str
    url: str
    model: str


def clean_query(raw: object) -> str:
    if not isinstance(raw, str):
        return ""
    return " ".join(raw.split())[:_MAX_QUERY]


def search_registered(request: HttpRequest, raw_query: object) -> list[SearchHit]:
    """Return viewable objects. Models without search_fields are skipped."""

    query = clean_query(raw_query)
    if len(query) < 2 or not request.user.is_active or not request.user.is_staff:
        return []
    hits: list[SearchHit] = []
    for model, model_admin in site._registry.items():
        if not getattr(model_admin, "search_fields", None):
            continue
        if not model_admin.has_view_permission(request):
            continue
        queryset, _distinct = model_admin.get_search_results(
            request,
            model_admin.get_queryset(request),
            query,
        )
        opts = model._meta
        verbose = str(opts.verbose_name_plural)
        for obj in queryset[:_PER_MODEL]:
            if not model_admin.has_view_permission(request, obj):
                continue
            try:
                url = reverse(
                    f"admin:{opts.app_label}_{opts.model_name}_change",
                    args=[obj.pk],
                )
            except NoReverseMatch:
                continue
            hits.append(SearchHit(label=str(obj)[:200], url=url, model=verbose))
            if len(hits) >= _MAX_HITS:
                return hits
    return hits
