from __future__ import annotations

import html
import smtplib
from email.message import EmailMessage

from .config import settings

SKIP_FIELDS = {"project_name", "admin_email", "form_subject"}


class MailConfigError(RuntimeError):
    pass


def _html_table(fields: dict[str, str]) -> str:
    rows: list[str] = []
    alt = False
    for raw_key, raw_value in fields.items():
        if not raw_value or raw_key in SKIP_FIELDS:
            continue
        key = raw_key.replace("_", " ").title()
        value = html.escape(raw_value).replace("\n", "<br>")
        bg = " background-color: #f3f3f3;" if alt else ""
        alt = not alt
        rows.append(
            f'<tr style="{bg}"><td style="padding: 10px; border: #e9e9e9 1px solid; width: 100px; '
            f'vertical-align: top;"><strong>{html.escape(key)}:</strong></td>'
            f'<td style="padding: 10px; border: #e9e9e9 1px solid;">{value}</td></tr>'
        )
    return f'<table style="width: 100%;">{"".join(rows)}</table>' if rows else ""


def send_contact_mail(fields: dict[str, str]) -> None:
    to_email = settings.contact_to_email.strip()
    smtp_host = settings.smtp_host.strip()
    if not to_email or not smtp_host:
        raise MailConfigError(
            "Email is not configured. Set CONTACT_TO_EMAIL and SMTP_HOST in the API environment."
        )

    body = _html_table(fields)
    if not body:
        raise ValueError("Please fill in the form before submitting.")

    sender_email = fields.get("email", "").strip()
    from_name = settings.contact_from_name.strip() or "Softsove"
    from_email = settings.contact_from_email.strip() or to_email
    subject = settings.contact_subject.strip() or "Message from Softsove"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    if sender_email:
        message["Reply-To"] = sender_email
    message.set_content("A new contact form message was submitted.")
    message.add_alternative(body, subtype="html")

    if settings.smtp_secure:
        server: smtplib.SMTP = smtplib.SMTP_SSL(smtp_host, settings.smtp_port, timeout=20)
    else:
        server = smtplib.SMTP(smtp_host, settings.smtp_port, timeout=20)
        server.starttls()

    try:
        if settings.smtp_user and settings.smtp_pass:
            server.login(settings.smtp_user, settings.smtp_pass)
        server.send_message(message)
    finally:
        server.quit()
