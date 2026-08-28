from __future__ import annotations

import html
import logging
import re
import smtplib
from email.message import EmailMessage

from .config import settings

SKIP_FIELDS = {"project_name", "admin_email", "form_subject"}
LABELS = {
    "name": "Who walked in",
    "email": "Where to ping",
    "option": "The plot",
    "message": "What they actually said",
    "phone": "The ring",
}
EMAIL_OK = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

BRAND = "#9d2e13"
HOVER = "#d5350e"
DARK = "#16171a"
CREAM = "#e9e6de"
PAPER = "#f1efe9"
MUTED = "#6c6c6c"
FONT = "'Cascadia Mono', 'Cascadia Code', 'Courier New', Courier, monospace"
SITE = "https://softsove.com"


class MailConfigError(RuntimeError):
    pass


def _label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").title())


def _first(fields: dict[str, str], key: str, fallback: str = "") -> str:
    return (fields.get(key) or "").strip() or fallback


def _shell(eyebrow: str, title: str, intro: str, inner: str, cta_href: str, cta_label: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Cascadia+Mono:wght@400;600&display=swap" rel="stylesheet">
  <title>{html.escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:{CREAM};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{CREAM};margin:0;padding:36px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:100%;background:{CREAM};border:2px solid {DARK};box-shadow:8px 8px 0 {DARK};">
          <tr>
            <td style="background:{BRAND};height:8px;font-size:0;line-height:0;">&nbsp;</td>
          </tr>
          <tr>
            <td style="padding:36px 40px 20px 40px;">
              <p style="margin:0 0 10px 0;font-size:12px;letter-spacing:0.2em;text-transform:uppercase;color:{BRAND};font-family:{FONT};">{html.escape(eyebrow)}</p>
              <p style="margin:0;font-size:12px;letter-spacing:0.32em;text-transform:uppercase;color:{DARK};font-family:{FONT};">Softsove</p>
              <h1 style="margin:16px 0 0 0;font-size:34px;line-height:1.15;font-weight:600;color:{DARK};font-family:{FONT};">{html.escape(title)}</h1>
              <p style="margin:16px 0 0 0;font-size:15px;line-height:1.7;color:{MUTED};font-family:{FONT};">{intro}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 40px 12px 40px;">{inner}</td>
          </tr>
          <tr>
            <td style="padding:12px 40px 16px 40px;">
              <a href="{html.escape(cta_href)}" style="display:inline-block;background:{BRAND};color:{CREAM};text-decoration:none;font-size:13px;letter-spacing:0.12em;text-transform:uppercase;padding:14px 26px;font-family:{FONT};border:2px solid {DARK};">{html.escape(cta_label)}</a>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 40px 36px 40px;">
              <p style="margin:0;font-size:12px;line-height:1.8;color:{MUTED};font-family:{FONT};">
                The Anand plot · 5th Floor, Aakruti Business Hub<br>
                <a href="mailto:care@softsove.com" style="color:{HOVER};text-decoration:none;">care@softsove.com</a>
                &nbsp;·&nbsp;+91 9978404123<br>
                <a href="{SITE}" style="color:{DARK};text-decoration:underline;">{SITE.replace("https://", "")}</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _field_blocks(fields: dict[str, str]) -> str:
    rows: list[str] = []
    for key, raw_value in fields.items():
        if not raw_value or key in SKIP_FIELDS:
            continue
        value = html.escape(raw_value).replace("\n", "<br>")
        if key == "email":
            value = (
                f'<a href="mailto:{html.escape(raw_value)}" '
                f'style="color:{HOVER};text-decoration:underline;">{html.escape(raw_value)}</a>'
            )
        rows.append(
            f"""
            <tr>
              <td style="padding:0 0 20px 0;">
                <p style="margin:0 0 6px 0;font-size:11px;letter-spacing:0.16em;text-transform:uppercase;color:{BRAND};font-family:{FONT};">{html.escape(_label(key))}</p>
                <p style="margin:0;font-size:16px;line-height:1.65;color:{DARK};font-family:{FONT};">{value}</p>
              </td>
            </tr>
            """
        )
    if not rows:
        return ""
    return f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};border:2px solid {DARK};">
      <tr>
        <td style="padding:28px 28px 8px 28px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{"".join(rows)}</table>
        </td>
      </tr>
    </table>
    """


def _studio_html(fields: dict[str, str]) -> str:
    name = html.escape(_first(fields, "name", "a brave stranger"))
    inner = _field_blocks(fields)
    if not inner:
        return ""
    sender = _first(fields, "email")
    cta = f"mailto:{sender}" if sender else f"mailto:{settings.contact_to_email}"
    return _shell(
        eyebrow="( Mail that refuses beige )",
        title="Someone poked the studio",
        intro=f"{name} dropped a line through Let's Get Weird. Don't leave a human on read.",
        inner=inner,
        cta_href=cta,
        cta_label="Write them back",
    )


def _visitor_html(fields: dict[str, str]) -> str:
    name = html.escape(_first(fields, "name", "you"))
    topic = html.escape(_first(fields, "option", "something un-boring"))
    inner = f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};border:2px solid {DARK};">
      <tr>
        <td style="padding:28px;">
          <p style="margin:0 0 14px 0;font-size:15px;line-height:1.75;color:{DARK};font-family:{FONT};">
            {name}, we got it. Your note about <strong>{topic}</strong> is on the pile, not in a void.
          </p>
          <p style="margin:0;font-size:15px;line-height:1.75;color:{MUTED};font-family:{FONT};">
            A human at Softsove will write back. Until then, boring stays illegal.
          </p>
        </td>
      </tr>
    </table>
    """
    return _shell(
        eyebrow="( No boring auto-replies )",
        title="We caught your hello",
        intro="This is the part where most studios send a beige template. We don't.",
        inner=inner,
        cta_href=f"{SITE}/lets-get-weird",
        cta_label="Stay in the plot",
    )


def _studio_plain(fields: dict[str, str]) -> str:
    lines = ["SOFTSOVE", "( Mail that refuses beige )", "Someone poked the studio", ""]
    for key, value in fields.items():
        if not value or key in SKIP_FIELDS:
            continue
        lines.append(f"{_label(key)}: {value}")
    lines.extend(["", "Write them back.", "The Anand plot · care@softsove.com"])
    return "\n".join(lines)


def _visitor_plain(fields: dict[str, str]) -> str:
    name = _first(fields, "name", "you")
    topic = _first(fields, "option", "something un-boring")
    return "\n".join(
        [
            "SOFTSOVE",
            "( No boring auto-replies )",
            "We caught your hello",
            "",
            f"{name}, we got it. Your note about {topic} is on the pile, not in a void.",
            "A human at Softsove will write back. Until then, boring stays illegal.",
            "",
            f"{SITE}/lets-get-weird",
            "The Anand plot · care@softsove.com",
        ]
    )


def _message(
    *,
    subject: str,
    to_email: str,
    html_body: str,
    plain: str,
    from_name: str,
    from_email: str,
    reply_to: str = "",
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = to_email
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(plain)
    message.add_alternative(html_body, subtype="html")
    return message


def send_contact_mail(fields: dict[str, str]) -> None:
    to_email = settings.contact_to_email.strip()
    smtp_host = settings.smtp_host.strip()
    if not to_email or not smtp_host:
        raise MailConfigError(
            "Email is not configured. Set CONTACT_TO_EMAIL and SMTP_HOST in the API environment."
        )

    studio_html = _studio_html(fields)
    if not studio_html:
        raise ValueError("Please fill in the form before submitting.")

    visitor_email = _first(fields, "email")
    visitor_name = _first(fields, "name")
    from_name = settings.contact_from_name.strip() or "Softsove"
    from_email = settings.contact_from_email.strip() or to_email

    studio_subject = "Someone poked the studio"
    if visitor_name:
        studio_subject = f"{studio_subject} — {visitor_name}"

    studio = _message(
        subject=studio_subject,
        to_email=to_email,
        html_body=studio_html,
        plain=_studio_plain(fields),
        from_name=from_name,
        from_email=from_email,
        reply_to=visitor_email,
    )

    thanks = None
    if visitor_email and EMAIL_OK.match(visitor_email):
        thanks = _message(
            subject="We caught your hello — boring can wait",
            to_email=visitor_email,
            html_body=_visitor_html(fields),
            plain=_visitor_plain(fields),
            from_name=from_name,
            from_email=from_email,
            reply_to=to_email,
        )

    if settings.smtp_secure:
        server: smtplib.SMTP = smtplib.SMTP_SSL(smtp_host, settings.smtp_port, timeout=20)
    else:
        server = smtplib.SMTP(smtp_host, settings.smtp_port, timeout=20)
        server.starttls()

    try:
        if settings.smtp_user and settings.smtp_pass:
            server.login(settings.smtp_user, settings.smtp_pass)
        server.send_message(studio)
        if thanks is not None:
            try:
                server.send_message(thanks)
            except Exception:
                logging.exception("Visitor hello-mail failed")
    finally:
        server.quit()
