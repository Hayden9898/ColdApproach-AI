"""
Factory that resolves the correct EmailProvider based on the sender's email domain.
Extensible: add new domain mappings for Outlook/Microsoft later.
"""

from app.services.email_provider import EmailProvider
from app.services.gmail_provider import GmailProvider
from app.services.ses_provider import SESProvider

# Domain -> Provider class mapping
_DOMAIN_PROVIDER_MAP = {
    "gmail.com": GmailProvider,
    "googlemail.com": GmailProvider,
    # Future: "outlook.com": OutlookProvider, "hotmail.com": OutlookProvider
}

_provider_instances: dict = {}


def get_provider(from_email: str) -> EmailProvider:
    """
    Determine the email provider from the sender's domain.
    @gmail.com / @googlemail.com -> GmailProvider
    Everything else              -> SESProvider (custom domain)
    """
    domain = from_email.strip().lower().split("@")[-1]
    provider_cls = _DOMAIN_PROVIDER_MAP.get(domain, SESProvider)
    cls_name = provider_cls.__name__

    if cls_name not in _provider_instances:
        _provider_instances[cls_name] = provider_cls()

    return _provider_instances[cls_name]
