"""Unit tests for phone validation and normalization."""
import pytest

from app.core.phone import normalize_phone, validate_phone_format


class TestValidatePhoneFormat:
    def test_valid_10_digits(self):
        validate_phone_format("8699999999")  # 10 digits — no error

    def test_valid_11_digits(self):
        validate_phone_format("86999999999")  # 11 digits

    def test_valid_13_digits_with_country_code(self):
        validate_phone_format("5586999999999")  # 13 digits

    def test_valid_with_formatting_characters(self):
        # Non-digits stripped: (86) 99999-9999 = 11 digits
        validate_phone_format("(86) 99999-9999")

    def test_invalid_too_short(self):
        with pytest.raises(ValueError, match="inválido"):
            validate_phone_format("12345")  # 5 digits

    def test_invalid_too_long(self):
        with pytest.raises(ValueError, match="inválido"):
            validate_phone_format("55869999999999")  # 14 digits

    def test_invalid_only_letters(self):
        with pytest.raises(ValueError, match="inválido"):
            validate_phone_format("abcdefghij")  # 0 digits after strip

    def test_invalid_empty_after_strip(self):
        with pytest.raises(ValueError, match="inválido"):
            validate_phone_format("abc-def")  # 0 digits

    def test_invalid_mixed_too_short(self):
        with pytest.raises(ValueError, match="inválido"):
            validate_phone_format("abc123def")  # 3 digits


class TestNormalizePhone:
    def test_adds_country_code_55(self):
        result = normalize_phone("86999999999")
        assert result == "5586999999999@s.whatsapp.net"

    def test_strips_non_digits(self):
        # (86) 99999-9999 → digits: 86999999999 (11) → prefixed: 5586999999999
        result = normalize_phone("(86) 99999-9999")
        assert result == "5586999999999@s.whatsapp.net"

    def test_does_not_double_country_code(self):
        result = normalize_phone("5586999999999")
        assert result == "5586999999999@s.whatsapp.net"

    def test_appends_whatsapp_suffix(self):
        result = normalize_phone("86999999999")
        assert result.endswith("@s.whatsapp.net")

    def test_passthrough_if_already_suffixed(self):
        already = "5586999999999@s.whatsapp.net"
        result = normalize_phone(already)
        assert result == already

    def test_strips_formatting_and_adds_prefix(self):
        result = normalize_phone("+55 (86) 9 9999-9999")
        assert result == "5586999999999@s.whatsapp.net"
