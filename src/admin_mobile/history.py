"""Phone timeline data for Django admin log entries."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime

from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.utils import formats, timezone
from django.utils.translation import gettext

_KIND = {
    ADDITION: "added",
    CHANGE: "changed",
    DELETION: "deleted",
}


def history_groups(entries: Iterable[object]) -> list[dict[str, object]]:
    """Group log rows by local day, newest day and newest row first."""

    items = [_describe(entry) for entry in entries]
    items.sort(key=lambda item: item["at"], reverse=True)
    groups: list[dict[str, object]] = []
    for item in items:
        day = item["day"]
        if groups and groups[-1]["day"] == day:
            rows = groups[-1]["items"]
            if isinstance(rows, list):
                rows.append(item)
            continue
        groups.append({"day": day, "label": item["day_label"], "items": [item]})
    return groups


def history_count(action_list: Iterable[object]) -> int:
    paginator = getattr(action_list, "paginator", None)
    total = getattr(paginator, "count", None)
    if isinstance(total, int):
        return total
    return len(list(action_list))


def _describe(entry: object) -> dict[str, object]:
    flag = int(getattr(entry, "action_flag", 0) or 0)
    kind = _KIND.get(flag, "note")
    fields = _changed_fields(getattr(entry, "change_message", "") or "")
    title = ""
    getter = getattr(entry, "get_change_message", None)
    if callable(getter):
        title = str(getter() or "").strip()
    if not title:
        title = _fallback_title(flag)
    moment = _local(getattr(entry, "action_time", None))
    user = getattr(entry, "user", None)
    username = ""
    full_name = ""
    if user is not None:
        username = str(user.get_username() or "")
        full = getattr(user, "get_full_name", None)
        if callable(full):
            full_name = str(full() or "")
    who = f"{username} ({full_name})" if username and full_name else username
    return {
        "kind": kind,
        "title": title,
        "fields": fields,
        "user": who,
        "when": formats.date_format(moment, "SHORT_DATETIME_FORMAT"),
        "at": moment,
        "day": moment.date(),
        "day_label": formats.date_format(moment, "SHORT_DATE_FORMAT"),
    }


def _fallback_title(flag: int) -> str:
    if flag == ADDITION:
        return gettext("Added.")
    if flag == DELETION:
        return gettext("Deleted.")
    if flag == CHANGE:
        return gettext("Changed.")
    return gettext("Updated.")


def _changed_fields(message: str) -> list[str]:
    if not message.startswith("["):
        return []
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    names: list[str] = []
    for part in payload:
        if not isinstance(part, dict):
            continue
        changed = part.get("changed")
        if not isinstance(changed, dict):
            continue
        raw_fields = changed.get("fields") or []
        if not isinstance(raw_fields, list):
            continue
        for name in raw_fields:
            if isinstance(name, str) and name and name not in names:
                names.append(gettext(name))
    return names


def _local(moment: object) -> datetime:
    if not isinstance(moment, datetime):
        moment = timezone.now()
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, timezone.get_current_timezone())
    return timezone.localtime(moment)
