"""Testes unitários para app/core/security.py."""
import re

import pytest

from app.core.security import generate_api_key, hash_api_key


class TestGenerateApiKey:
    def test_format_prefix(self):
        key = generate_api_key()
        assert key.startswith("zapi_")

    def test_format_length(self):
        key = generate_api_key()
        # "zapi_" (5) + 32 hex chars = 37 total
        assert len(key) == 37

    def test_format_hex_chars(self):
        key = generate_api_key()
        hex_part = key[len("zapi_"):]
        assert re.fullmatch(r"[0-9a-f]{32}", hex_part)

    def test_uniqueness(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100


class TestHashApiKey:
    def test_same_input_same_hash(self):
        h1 = hash_api_key("zapi_abc123", "my-salt")
        h2 = hash_api_key("zapi_abc123", "my-salt")
        assert h1 == h2

    def test_different_keys_different_hashes(self):
        h1 = hash_api_key("zapi_key1", "salt")
        h2 = hash_api_key("zapi_key2", "salt")
        assert h1 != h2

    def test_different_salts_different_hashes(self):
        h1 = hash_api_key("zapi_key", "salt1")
        h2 = hash_api_key("zapi_key", "salt2")
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = hash_api_key("zapi_key", "salt")
        assert re.fullmatch(r"[0-9a-f]{64}", h)
