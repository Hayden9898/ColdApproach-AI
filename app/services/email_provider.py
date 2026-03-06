"""
Abstract base for email sending providers.
Each provider (Gmail, SES, future Outlook) implements this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class EmailProvider(ABC):

    @abstractmethod
    def send(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email immediately.
        Returns {"success": bool, "message_id": str|None, "error": str|None}
        """
        ...

    @abstractmethod
    def validate_sender(self, from_email: str) -> Dict[str, Any]:
        """
        Check whether the sender is authorized to send through this provider.
        Returns {"verified": bool, "detail": str}
        """
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g. 'gmail', 'ses')."""
        ...
