import pytest
from app.core.phone import normalize_phone


def test_strips_spaces():
    assert normalize_phone("55 86 99999 9999") == "5586999999999@s.whatsapp.net"


def test_strips_parentheses_and_hyphens():
    assert normalize_phone("(86) 99999-9999") == "5586999999999@s.whatsapp.net"


def test_adds_country_code_when_missing():
    assert normalize_phone("86999999999") == "5586999999999@s.whatsapp.net"


def test_does_not_duplicate_country_code():
    assert normalize_phone("5586999999999") == "5586999999999@s.whatsapp.net"


def test_strips_plus_sign():
    assert normalize_phone("+5586999999999") == "5586999999999@s.whatsapp.net"


def test_already_normalized_passes_through():
    assert normalize_phone("5586999999999@s.whatsapp.net") == "5586999999999@s.whatsapp.net"


def test_strips_all_special_chars():
    assert normalize_phone("+55 (86) 9.9999-9999") == "5586999999999@s.whatsapp.net"
