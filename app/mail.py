from __future__ import annotations

import html
import smtplib
from email.message import EmailMessage

from .config import settings

SKIP_FIELDS = {"project_name", "admin_email", "form_subject"}
LABELS = {
    "name": "Name",
    "email": "Email",
    "option": "Topic",
    "message": "Message",
    "phone": "Phone",
}

BRAND = "#9d2e13"
HOVER = "#d5350e"
DARK = "#16171a"
CREAM = "#e9e6de"
MUTED = "#9a958c"
FONT = "'Cascadia Mono', 'Cascadia Code', 'Courier New', Courier, monospace"


class MailConfigError(RuntimeError):
    pass


def _label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").title())


def _plain_text(fields: dict[str, str]) -> str:
    lines = ["SOFTSOVE", "( No boring hellos )", "Let's Get Weird", ""]
    for key, value in fields.items():
        if not value or key in SKIP_FIELDS:
            continue
        lines.append(f"{_label(key)}: {value}")
    lines.extend(["", "Reply to this email to continue the conversation.", "care@softsove.com"])
    return "\n".join(lines)


def _html_email(fields: dict[str, str]) -> str:
    blocks: list[str] = []
    for key, raw_value in fields.items():
        if not raw_value or key in SKIP_FIELDS:
            continue
        value = html.escape(raw_value).replace("\n", "<br>")
        if key == "email":
            value = (
                f'<a href="mailto:{html.escape(raw_value)}" '
                f'style="color:{HOVER};text-decoration:underline;">{html.escape(raw_value)}</a>'
            )
        blocks.append(
            f"""
            <tr>
              <td style="padding:0 0 22px 0;">
                <p style="margin:0 0 8px 0;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:{BRAND};font-family:{FONT};">{html.escape(_label(key))}</p>
                <p style="margin:0;font-size:16px;line-height:1.6;color:{CREAM};font-family:{FONT};">{value}</p>
              </td>
            </tr>
            """
        )
    if not blocks:
        return ""

    sender_email = (fields.get("email") or "").strip()
    sender_name = html.escape((fields.get("name") or "Someone").strip() or "Someone")
    reply_href = f"mailto:{html.escape(sender_email)}" if sender_email else "mailto:care@softsove.com"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Cascadia+Mono:wght@400;600&display=swap" rel="stylesheet">
  <title>Let's Get Weird</title>
</head>
<body style="margin:0;padding:0;background:{DARK};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{DARK};margin:0;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:100%;background:{DARK};border:1px solid {BRAND};">
          <tr>
            <td style="background:{BRAND};height:6px;font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:36px 40px 24px 40px;">
              <p style="margin:0 0 10px 0;font-size:12px;letter-spacing:0.22em;text-transform:uppercase;color:{BRAND};font-family:{FONT};">( No boring hellos )</p>
              <p style="margin:0;font-size:13px;letter-spacing:0.28em;text-transform:uppercase;color:{CREAM};font-family:{FONT};">Softsove</p>
              <h1 style="margin:18px 0 0 0;font-size:32px;line-height:1.15;font-weight:600;color:{CREAM};font-family:{FONT};">Let's Get Weird</h1>
              <p style="margin:14px 0 0 0;font-size:14px;line-height:1.7;color:{MUTED};font-family:{FONT};">A new note landed on the desk from {sender_name}. Time to make boring illegal.</p>
            </td>
          </tr>
          <tr>
            <td style="padding:0 40px 8px 40px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-left:3px solid {BRAND};background:#1d1e22;">
                <tr>
                  <td style="padding:28px 28px 6px 28px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      {"".join(blocks)}
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 40px 12px 40px;">
              <a href="{reply_href}" style="display:inline-block;background:{BRAND};color:{CREAM};text-decoration:none;font-size:13px;letter-spacing:0.12em;text-transform:uppercase;padding:14px 28px;font-family:{FONT};">Reply to this human</a>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 40px 36px 40px;">
              <p style="margin:0;font-size:12px;line-height:1.7;color:{MUTED};font-family:{FONT};">
                Softsove desk<br>
                5th Floor, Aakruti Business Hub, Anand<br>
                <a href="mailto:care@softsove.com" style="color:{HOVER};text-decoration:none;">care@softsove.com</a>
                &nbsp;·&nbsp;+91 9978404123
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_contact_mail(fields: dict[str, str]) -> None:
    to_email = settings.contact_to_email.strip()
    smtp_host = settings.smtp_host.strip()
    if not to_email or not smtp_host:
        raise MailConfigError(
            "Email is not configured. Set CONTACT_TO_EMAIL and SMTP_HOST in the API environment."
        )

    body = _html_email(fields)
    if not body:
        raise ValueError("Please fill in the form before submitting.")

    sender_email = fields.get("email", "").strip()
    sender_name = (fields.get("name") or "").strip()
    from_name = settings.contact_from_name.strip() or "Softsove"
    from_email = settings.contact_from_email.strip() or to_email
    subject = settings.contact_subject.strip() or "Let's Get Weird"
    if sender_name:
        subject = f"{subject} — {sender_name}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    if sender_email:
        message["Reply-To"] = sender_email
    message.set_content(_plain_text(fields))
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
