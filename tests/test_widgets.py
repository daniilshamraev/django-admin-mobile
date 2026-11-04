from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError
from django.forms import SplitDateTimeField
from django.test import override_settings
from django.utils import timezone as dj_tz

from admin_mobile.widgets import (
    ISO_DATE_INPUT_FORMATS,
    ISO_TIME_INPUT_FORMATS,
    NativeDateInput,
    NativeSplitDateTimeWidget,
    NativeTimeInput,
)

MOSCOW = ZoneInfo("Europe/Moscow")


def test_native_date_input_renders_iso() -> None:
    html = NativeDateInput().render("published_on", date(2024, 1, 2))
    assert html is not None
    assert 'type="date"' in html
    assert 'value="2024-01-02"' in html
    assert "vDateField" not in html


def test_native_date_input_empty_is_blank() -> None:
    html = NativeDateInput().render("published_on", None)
    assert html is not None
    assert "None" not in html
    assert 'type="date"' in html


def test_native_time_input_renders_seconds() -> None:
    html = NativeTimeInput().render("starts_at", time(8, 15, 1))
    assert html is not None
    assert 'type="time"' in html
    assert 'value="08:15:01"' in html
    assert 'step="1"' in html


def test_split_widget_converts_to_current_timezone() -> None:
    moment = datetime(2024, 6, 15, 12, 0, tzinfo=timezone.utc)
    html = NativeSplitDateTimeWidget().render("scheduled_for", moment)
    assert html is not None
    assert 'type="date"' in html
    assert 'type="time"' in html
    assert 'value="2024-06-15"' in html
    assert 'value="15:00:00"' in html
    assert "Europe/Moscow" in html


@override_settings(USE_TZ=False, TIME_ZONE="Europe/Moscow")
def test_split_widget_without_tz_skips_timezone_note() -> None:
    html = NativeSplitDateTimeWidget().render(
        "scheduled_for",
        datetime(2024, 6, 15, 9, 30, 0),
    )
    assert html is not None
    assert 'value="2024-06-15"' in html
    assert 'value="09:30:00"' in html
    assert "timezonewarning" not in html


def test_split_field_round_trip_is_aware() -> None:
    field = SplitDateTimeField(
        widget=NativeSplitDateTimeWidget(),
        input_date_formats=list(ISO_DATE_INPUT_FORMATS),
        input_time_formats=list(ISO_TIME_INPUT_FORMATS),
        localize=False,
    )
    value = field.clean(["2024-06-15", "15:00:00"])
    assert dj_tz.is_aware(value)
    assert value.astimezone(timezone.utc) == datetime(
        2024, 6, 15, 12, 0, tzinfo=timezone.utc
    )
    assert value.astimezone(MOSCOW).hour == 15


def test_split_field_accepts_time_without_seconds() -> None:
    field = SplitDateTimeField(
        widget=NativeSplitDateTimeWidget(),
        input_date_formats=list(ISO_DATE_INPUT_FORMATS),
        input_time_formats=list(ISO_TIME_INPUT_FORMATS),
    )
    value = field.clean(["2024-06-15", "15:04"])
    assert value.astimezone(MOSCOW).minute == 4


def test_split_field_rejects_locale_date() -> None:
    field = SplitDateTimeField(
        widget=NativeSplitDateTimeWidget(),
        input_date_formats=list(ISO_DATE_INPUT_FORMATS),
        input_time_formats=list(ISO_TIME_INPUT_FORMATS),
    )
    with pytest.raises(ValidationError):
        field.clean(["15.06.2024", "15:00:00"])


def test_decompress_drops_microseconds() -> None:
    moment = datetime(2024, 6, 15, 12, 0, 1, 250000, tzinfo=timezone.utc)
    parts = NativeSplitDateTimeWidget().decompress(moment)
    assert parts[0] == date(2024, 6, 15)
    assert parts[1] == time(15, 0, 1)


def test_decompress_empty_values() -> None:
    widget = NativeSplitDateTimeWidget()
    assert widget.decompress(None) == [None, None]
    assert widget.decompress("") == [None, None]
