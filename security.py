from __future__ import annotations

import hashlib
import hmac
import secrets

PREFIX = "pbkdf2_sha256"
ITERATIONS = 260_000


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not any(c.isupper() for c in password):
        return False, "Incluye al menos una letra mayúscula."
    if not any(c.islower() for c in password):
        return False, "Incluye al menos una letra minúscula."
    if not any(c.isdigit() for c in password):
        return False, "Incluye al menos un número."
    return True, ""


def hash_password(password: str) -> str:
    """Genera un hash irreversible con una sal aleatoria por contraseña."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt), ITERATIONS
    ).hex()
    return f"{PREFIX}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    """Compara una contraseña sin exponerla ni usar comparaciones vulnerables."""
    if not stored:
        return False
    # La migración heredada ocurre al arrancar; aquí nunca se acepta texto plano.
    if not stored.startswith(PREFIX + "$"):
        return False
    try:
        _, iterations, salt, expected = stored.split("$", 3)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def reset_code() -> str:
    """Crea un código temporal con un generador criptográficamente seguro."""
    return f"{secrets.randbelow(1_000_000):06d}"


def token_hash(code: str) -> str:
    """Evita guardar códigos de recuperación utilizables."""
    return hashlib.sha256(code.strip().encode()).hexdigest()
