import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from admin_mobile.conf import AdminMobileSettings, get_config


def test_defaults_when_setting_missing() -> None:
    config = get_config()
    assert config == AdminMobileSettings()
    assert config.use_native_datetime is False
    assert config.changelist_cards is True


@override_settings(ADMIN_MOBILE={"STICKY_SUBMIT": False, "USE_NATIVE_DATETIME": True})
def test_partial_override_keeps_other_defaults() -> None:
    config = get_config()
    assert config.sticky_submit is False
    assert config.use_native_datetime is True
    assert config.touch_targets is True


@override_settings(ADMIN_MOBILE=["ENABLED"])
def test_non_dict_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="dict"):
        get_config()


@override_settings(ADMIN_MOBILE={"ENABLED": "yes"})
def test_non_bool_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="bool"):
        get_config()


@override_settings(ADMIN_MOBILE={"CARDS": True})
def test_unknown_key_is_rejected() -> None:
    with pytest.raises(ImproperlyConfigured, match="CARDS"):
        get_config()


@override_settings(ADMIN_MOBILE=None)
def test_explicit_none_uses_defaults() -> None:
    assert get_config() == AdminMobileSettings()
