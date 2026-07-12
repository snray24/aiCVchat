"""Allowlist service for email authorization."""
from pathlib import Path
from app.core.security import decrypt_allowlist
from app.core.config import settings
from app.core.logging import logger


class AllowlistService:
    """Service for managing and checking email allowlist."""
    
    def __init__(self):
        self.allowlist_path = Path("backend/data/allowed_emails.enc")
        self._cached_allowlist: set[str] | None = None
    
    def load_allowlist(self) -> set[str]:
        """Load and decrypt the allowlist from file."""
        if self._cached_allowlist is not None:
            return self._cached_allowlist
        
        if not self.allowlist_path.exists():
            logger.warning(f"Allowlist file not found: {self.allowlist_path}")
            return set()
        
        try:
            with open(self.allowlist_path, "r") as f:
                encrypted_data = f.read()
            
            self._cached_allowlist = decrypt_allowlist(encrypted_data)
            logger.info(f"Loaded {len(self._cached_allowlist)} emails from allowlist")
            return self._cached_allowlist
            
        except Exception as e:
            logger.error(f"Failed to load allowlist: {e}")
            return set()
    
    def is_email_allowed(self, email: str) -> bool:
        """Check if an email is in the allowlist."""
        normalized_email = email.strip().lower()
        allowlist = self.load_allowlist()
        return normalized_email in allowlist
    
    def reload_allowlist(self) -> None:
        """Force reload the allowlist from file."""
        self._cached_allowlist = None
        self.load_allowlist()


allowlist_service = AllowlistService()
