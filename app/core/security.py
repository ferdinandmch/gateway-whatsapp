import hashlib
import secrets


def generate_api_key() -> str:
    return f"zapi_{secrets.token_hex(16)}"


def hash_api_key(raw_key: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}{raw_key}".encode()).hexdigest()
