"""Security utilities for encryption/decryption."""
from cryptography.fernet import Fernet
from app.core.config import settings
from app.core.logging import logger


def get_fernet() -> Fernet:
    """Get Fernet cipher instance from encryption key."""
    if not settings.allowlist_encryption_key:
        raise ValueError("ALLOWLIST_ENCRYPTION_KEY environment variable not set")
    return Fernet(settings.allowlist_encryption_key.encode())


def encrypt_text(text: str) -> str:
    """Encrypt text using Fernet symmetric encryption."""
    fernet = get_fernet()
    encrypted = fernet.encrypt(text.encode())
    return encrypted.decode()


def decrypt_text(encrypted_text: str) -> str:
    """Decrypt text using Fernet symmetric encryption."""
    fernet = get_fernet()
    decrypted = fernet.decrypt(encrypted_text.encode())
    return decrypted.decode()


def encrypt_allowlist(emails: list[str]) -> str:
    """Encrypt a list of emails into a single string."""
    email_text = "\n".join(email.strip().lower() for email in emails if email.strip())
    return encrypt_text(email_text)


def decrypt_allowlist(encrypted_data: str) -> set[str]:
    """Decrypt encrypted allowlist and return set of normalized emails."""
    try:
        decrypted = decrypt_text(encrypted_data)
        emails = set()
        for line in decrypted.split("\n"):
            email = line.strip().lower()
            if email:
                emails.add(email)
        return emails
    except Exception as e:
        logger.error(f"Failed to decrypt allowlist: {e}")
        return set()
