"""HTML5 date and time widgets that keep Django's split-field validation."""

from __future__ import annotations

from datetime import datetime

from django import forms
from django.conf import settings
from django.forms.utils import to_current_timezone
from django.utils import timezone
from django.utils.translation import gettext

ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_TIME_FORMAT = "%H:%M:%S"
ISO_DATE_INPUT_FORMATS: tuple[str, ...] = (ISO_DATE_FORMAT,)
ISO_TIME_INPUT_FORMATS: tuple[str, ...] = (ISO_TIME_FORMAT, "%H:%M", "%H:%M:%S.%f")


def _merge_attrs(
    base: dict[str, str],
    extra: dict[str, str] | None,
) -> dict[str, str]:
    if not extra:
        return dict(base)
    merged = {**base, **extra}
    base_class = base.get("class", "")
    extra_class = extra.get("class", "")
    if base_class and extra_class:
        merged["class"] = f"{base_class} {extra_class}"
    return merged


class NativeDateInput(forms.DateInput):
    """``<input type="date">`` that always speaks ISO ``YYYY-MM-DD``."""

    input_type = "date"

    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        format: str | None = None,
    ) -> None:
        super().__init__(
            attrs=_merge_attrs({"class": "admin-mobile-native"}, attrs),
            format=format or ISO_DATE_FORMAT,
        )


class NativeTimeInput(forms.TimeInput):
    """``<input type="time">`` with seconds so Django can round-trip them."""

    input_type = "time"

    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        format: str | None = None,
    ) -> None:
        super().__init__(
            attrs=_merge_attrs(
                {"class": "admin-mobile-native", "step": "1"},
                attrs,
            ),
            format=format or ISO_TIME_FORMAT,
        )


class NativeSplitDateTimeWidget(forms.SplitDateTimeWidget):
    """Date plus time native inputs. Compression stays on ``SplitDateTimeField``."""

    template_name = "admin_mobile/widgets/split_datetime.html"
    supports_microseconds = False

    def __init__(
        self,
        attrs: dict[str, str] | None = None,
        date_format: str | None = None,
        time_format: str | None = None,
        date_attrs: dict[str, str] | None = None,
        time_attrs: dict[str, str] | None = None,
    ) -> None:
        # Skip SplitDateTimeWidget.__init__: it would build type=text inputs.
        forms.MultiWidget.__init__(
            self,
            widgets=(
                NativeDateInput(
                    attrs=date_attrs,
                    format=date_format or ISO_DATE_FORMAT,
                ),
                NativeTimeInput(
                    attrs=time_attrs,
                    format=time_format or ISO_TIME_FORMAT,
                ),
            ),
            attrs=attrs,
        )

    def decompress(self, value: object) -> list[object]:
        if not isinstance(value, datetime):
            return [None, None]
        # HTML time inputs reject microseconds; admin's split widget drops them too.
        current = to_current_timezone(value)
        return [current.date(), current.time().replace(microsecond=0)]

    def get_context(
        self,
        name: str,
        value: object,
        attrs: dict[str, str] | None,
    ) -> dict[str, object]:
        context = super().get_context(name, value, attrs)
        context["date_label"] = gettext("Date:")
        context["time_label"] = gettext("Time:")
        if settings.USE_TZ:
            context["timezone_name"] = timezone.get_current_timezone_name()
        else:
            context["timezone_name"] = ""
        return context
