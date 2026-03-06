"""
Abstract base for email sending providers.
Each provider (Gmail, SES, future Outlook) implements this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class EmailProvider(ABC):

    @abstractmethod
    def send(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        reply_to: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Send an email immediately.

        Args:
            html_body: Optional HTML version of the email body.
            attachments: List of (filename, file_bytes, mime_type) tuples.

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
