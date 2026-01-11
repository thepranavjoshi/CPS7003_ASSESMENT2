from __future__ import annotations

import base64
import hashlib
import os

try:
    import bcrypt  # type: ignore
    _HAS_BCRYPT = True
except Exception:
    bcrypt = None
    _HAS_BCRYPT = False

_PBKDF2_ITERATIONS = 210_000

def hash_password(password: str) -> str:
    """Return a portable password hash string.

    Prefer bcrypt when available (allowed at 80-100 level), otherwise PBKDF2-HMAC-SHA256.
    """
    password_bytes = password.encode("utf-8")

    if _HAS_BCRYPT:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return "bcrypt$" + hashed.decode("utf-8")

    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, _PBKDF2_ITERATIONS, dklen=32)
    return "pbkdf2$%d$%s$%s" % (
        _PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(dk).decode("ascii"),
    )

def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")

    if password_hash.startswith("bcrypt$"):
        if not _HAS_BCRYPT:
            return False
        stored = password_hash.split("$", 1)[1].encode("utf-8")
        return bool(bcrypt.checkpw(password_bytes, stored))

    if password_hash.startswith("pbkdf2$"):
        _, iters_s, salt_b64, dk_b64 = password_hash.split("$", 3)
        iters = int(iters_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(dk_b64.encode("ascii"))
        dk = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, iters, dklen=len(expected))
        return hashlib.compare_digest(dk, expected)

    return False
