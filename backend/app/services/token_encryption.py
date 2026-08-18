"""
Symmetric encryption for OAuth tokens at rest (social_connections table).

Uses Fernet (AES-128-CBC + HMAC, from the `cryptography` package) rather
than storing access/refresh tokens as plaintext — these are real
credentials that let someone post as @womensventfund's connected
accounts, not low-stakes data.

TOKEN_ENCRYPTION_KEY must be a Fernet key (44-char urlsafe-base64 string).
Generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
Set it on Railway (backend service, private var) — never commit it, never
put it in a NEXT_PUBLIC_* frontend var. Losing this key makes every
already-stored token unrecoverable — reconnecting the account is the
only recovery path, so treat it like a real secret, not a throwaway one.
"""

import os

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    key = os.getenv("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise ValueError(
            "TOKEN_ENCRYPTION_KEY environment variable not set — required to "
            "store/read OAuth tokens. Generate one with: python -c "
            '"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode())


def encrypt_token(plaintext: str) -> str:
    """Encrypts a token for storage. Returns a string safe for a Text column."""
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypts a token read from storage. Raises ValueError if the stored
    value can't be decrypted with the current TOKEN_ENCRYPTION_KEY (e.g.
    the key was rotated without re-encrypting existing rows)."""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError(
            "Could not decrypt stored token — TOKEN_ENCRYPTION_KEY may have "
            "changed since this token was stored. The connection will need "
            "to be reconnected."
        )
