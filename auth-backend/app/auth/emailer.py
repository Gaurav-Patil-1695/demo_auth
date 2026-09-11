from __future__ import annotations

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config.settings import settings


def _build_reset_link(raw_token: str) -> str:
    """Construct the password-reset URL from APP_BASE_URL and the raw token."""
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/reset-password?token={raw_token}"


def _build_plain_text_body(reset_link: str) -> str:
    return (
        "You requested a password reset.\n\n"
        "Click the link below to reset your password:\n"
        f"{reset_link}\n\n"
        "This link will expire in 60 minutes.\n\n"
        "If you did not request a password reset, "
        "you can safely ignore this email."
    )


def _build_html_body(reset_link: str) -> str:
    return (
        "<!DOCTYPE html>"
        "<html>"
        "<body>"
        "<p>You requested a password reset.</p>"
        "<p>Click the link below to reset your password:</p>"
        f'<p><a href=\"{reset_link}\">Reset my password</a></p>'
        "<p>This link will expire in 60 minutes.</p>"
        "<p>If you did not request a password reset, "
        "you can safely ignore this email.</p>"
        "</body>"
        "</html>"
    )


async def send_password_reset_email(email: str, raw_token: str) -> None:
    """Send the password-reset email to *email* containing a link with *raw_token*.

    Builds the reset link as ``APP_BASE_URL/reset-password?token=<raw_token>``
    and sends it via SMTP using the SMTP_* settings.

    This function is intentionally synchronous under the hood (smtplib) because
    an async SMTP library is not in requirements.txt.  It is declared async so
    callers can ``await`` it uniformly and it can be swapped for an async
    implementation later without changing call-sites.
    """
    reset_link = _build_reset_link(raw_token)

    message = MIMEMultipart("alternative")
    message["Subject"] = "Reset your password"
    message["From"] = settings.SMTP_FROM
    message["To"] = email

    plain_part = MIMEText(_build_plain_text_body(reset_link), "plain", "utf-8")
    html_part = MIMEText(_build_html_body(reset_link), "html", "utf-8")

    # Clients render the last attached part first; HTML is preferred.
    message.attach(plain_part)
    message.attach(html_part)

    smtp_cls = smtplib.SMTP_SSL if settings.SMTP_TLS else smtplib.SMTP  # type: ignore[assignment]

    with smtp_cls(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if not settings.SMTP_TLS and settings.SMTP_STARTTLS:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.sendmail(settings.SMTP_FROM, [email], message.as_string())
