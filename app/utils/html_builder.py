"""
Markdown-to-HTML converter and email wrapper for producing
professional HTML emails with inline styles.
"""

import re
from typing import Optional


def markdown_to_html(text: str) -> str:
    """
    Convert lightweight markdown conventions to inline-styled HTML.

    Supported:
        **bold** → <strong>
        Lines starting with '- ' → <ul><li> blocks
        Double newlines → <p> paragraph breaks
    """
    # Escape HTML entities first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Bold: **text** → <strong>text</strong>
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Split into paragraphs on double newlines
    paragraphs = re.split(r"\n{2,}", text.strip())

    html_parts = []
    for para in paragraphs:
        lines = para.strip().split("\n")

        # Check if this paragraph is a bullet list
        if all(line.strip().startswith("- ") for line in lines if line.strip()):
            items = "".join(
                f'<li style="margin-bottom:4px;">{line.strip()[2:]}</li>'
                for line in lines
                if line.strip()
            )
            html_parts.append(
                f'<ul style="margin:8px 0;padding-left:20px;">{items}</ul>'
            )
        else:
            # Convert single newlines within a paragraph to <br>
            content = "<br>\n".join(line.strip() for line in lines)
            html_parts.append(f'<p style="margin:0 0 12px 0;">{content}</p>')

    return "\n".join(html_parts)


def wrap_html_email(
    body_html: str,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    sender_name: Optional[str] = None,
) -> str:
    """
    Wrap converted HTML body in a minimal HTML document with
    inline styles (Gmail-like appearance) and a footer with
    clickable LinkedIn / GitHub links.
    """
    # Build footer links
    footer_links = []
    if linkedin_url:
        footer_links.append(
            f'<a href="{linkedin_url}" style="color:#1a73e8;text-decoration:underline;">LinkedIn</a>'
        )
    if github_url:
        footer_links.append(
            f'<a href="{github_url}" style="color:#1a73e8;text-decoration:underline;">GitHub</a>'
        )

    footer_html = ""
    if footer_links:
        separator = ' <span style="color:#999;">&nbsp;|&nbsp;</span> '
        footer_html = (
            '<div style="margin-top:24px;padding-top:12px;'
            'border-top:1px solid #e0e0e0;font-size:13px;color:#666;">'
            f'{separator.join(footer_links)}'
            "</div>"
        )

    return (
        "<!DOCTYPE html>"
        '<html><head><meta charset="utf-8"></head>'
        '<body style="font-family:Arial,Helvetica,sans-serif;'
        "font-size:15px;color:#202124;line-height:1.6;"
        'margin:0;padding:0;">'
        f"{body_html}"
        f"{footer_html}"
        "</body></html>"
    )


def build_plain_text_fallback(
    body: str,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
) -> str:
    """
    Build a plain-text version of the email.
    Strips **bold** markers and appends footer links as plain URLs.
    """
    # Strip bold markers
    plain = body.replace("**", "")

    # Append footer links
    links = []
    if linkedin_url:
        links.append(f"LinkedIn: {linkedin_url}")
    if github_url:
        links.append(f"GitHub: {github_url}")

    if links:
        plain += "\n\n---\n" + "\n".join(links)

    return plain
