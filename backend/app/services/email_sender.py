"""
Minimal transactional email sender via Gmail/Google Workspace SMTP —
used only for the approver "forgot passcode" reset link (see
routers/approvers.py). Not a marketing/bulk-send system — that's the
separate, still-undecided Vertical Response eblast question (see
docs/PROJECT_CONTEXT.md's Open Questions).

Requires SMTP_USERNAME (the sending account's address) and
SMTP_APP_PASSWORD (a Google Account app-specific password, generated
under that account's Security settings — requires 2FA enabled on the
sending account). Uses smtplib + Gmail's SMTP relay directly, no
third-party email API/vendor account.
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def _get_smtp_credentials() -> tuple[str, str]:
    username = os.getenv("SMTP_USERNAME")
    app_password = os.getenv("SMTP_APP_PASSWORD")
    if not username or not app_password:
        raise ValueError(
            "SMTP_USERNAME / SMTP_APP_PASSWORD environment variables not set — required to send "
            "passcode reset emails. Generate an app password at myaccount.google.com/apppasswords "
            "for the account that should send these (requires 2FA enabled on that account)."
        )
    return username, app_password


def send_passcode_reset_email(to_email: str, approver_name: str, reset_url: str) -> None:
    """Sends the one-time reset link. Raises on any SMTP failure — the
    caller (POST /api/approvers/forgot-passcode) should not reveal
    whether the send actually succeeded in its response (same reasoning
    as not revealing whether an email address is a known approver)."""
    username, app_password = _get_smtp_credentials()

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

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(username, app_password)
        server.send_message(message)
