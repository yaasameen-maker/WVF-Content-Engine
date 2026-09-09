"""
Minimal transactional email sender via SMTP — used only for the approver
"forgot passcode" reset link (see routers/approvers.py). Not a
marketing/bulk-send system — that's the separate, still-undecided
Vertical Response eblast question (see docs/PROJECT_CONTEXT.md's Open
Questions).

Host/port/security are configurable rather than hardcoded to one
provider: wvf-ny.org's mail is hosted on Microsoft 365 (confirmed via
MX record, Sept 2026), not Google Workspace as originally assumed, and
the actual sending account used for this (approver's own email, or a
Pursuit account in the interim) may be on a third provider entirely.
Whichever account sends these needs SMTP AUTH enabled — some Microsoft
365 tenants block SMTP basic auth by default (an admin-side setting,
not something this app can work around).

Requires SMTP_USERNAME (the sending account's address) and
SMTP_APP_PASSWORD (an app-specific password — Google requires 2FA +
an App Password from myaccount.google.com/apppasswords; Microsoft 365
requires an "App Password" under the account's Security info, only
available if the tenant has Security Defaults / per-user MFA enabled
and SMTP AUTH is not blocked at the tenant level). Optional
SMTP_HOST/SMTP_PORT override the default (Gmail's relay); for Microsoft
365 use smtp.office365.com:587 (STARTTLS, not SMTP_SSL).
"""

import os
import smtplib
from email.message import EmailMessage

DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 465


def _get_smtp_settings() -> tuple[str, str, str, int]:
    username = os.getenv("SMTP_USERNAME")
    app_password = os.getenv("SMTP_APP_PASSWORD")
    if not username or not app_password:
        raise ValueError(
            "SMTP_USERNAME / SMTP_APP_PASSWORD environment variables not set — required to send "
            "passcode reset emails. See email_sender.py's module docstring for how to generate an "
            "app password for the sending account's provider."
        )
    host = os.getenv("SMTP_HOST", DEFAULT_SMTP_HOST)
    port = int(os.getenv("SMTP_PORT", str(DEFAULT_SMTP_PORT)))
    return username, app_password, host, port


def send_passcode_reset_email(to_email: str, approver_name: str, reset_url: str) -> None:
    """Sends the one-time reset link. Raises on any SMTP failure — the
    caller (POST /api/approvers/forgot-passcode) should not reveal
    whether the send actually succeeded in its response (same reasoning
    as not revealing whether an email address is a known approver)."""
    username, app_password, host, port = _get_smtp_settings()

    message = EmailMessage()
    message["Subject"] = "WVF Content Engine — reset your approval passcode"
    message["From"] = username
    message["To"] = to_email
    message.set_content(
        f"Hi {approver_name},\n\n"
        f"Someone requested a passcode reset for your WVF Content Engine approver account.\n\n"
        f"Reset your passcode here (this link works once, and expires in 30 minutes):\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, you can ignore this email — your current passcode still works."
    )

    # Port 465 is implicit TLS (SMTP_SSL) — Gmail's relay. Port 587 is
    # STARTTLS (plaintext connect, then upgrade) — Microsoft 365's relay
    # and most other providers. 465 with STARTTLS or 587 with SMTP_SSL
    # both fail silently/hang, so the port picks the right client.
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(username, app_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, app_password)
            server.send_message(message)
