"""SMTP email sender."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.logging import get_logger

log = get_logger("newsletter.sender")


def send_email(subject: str, html: str, plaintext: str, recipient: str) -> None:
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASS]):
        raise RuntimeError("SMTP credentials not configured (SMTP_HOST, SMTP_USER, SMTP_PASS required)")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_FROM or settings.SMTP_USER
    msg["To"] = recipient

    msg.attach(MIMEText(plaintext, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    port = settings.SMTP_PORT
    host = settings.SMTP_HOST

    if port == 465:
        with smtplib.SMTP_SSL(host, port) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(msg["From"], [recipient], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(msg["From"], [recipient], msg.as_string())

    log.info("email sent", recipient=recipient, subject=subject)
