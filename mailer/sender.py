"""
email/sender.py — SMTP email sender for approved outreach messages.
Uses built-in smtplib — no extra packages needed.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config


def send_email(to: str, subject: str, body: str, html_body: str = None) -> bool:
    """
    Send an email via SMTP.
    Returns True on success, False on failure.
    Logs failure reason but never raises — caller must check return value.
    """
    if not config.EMAIL_ENABLED:
        print(f"[Email] Skipped — EMAIL_USER/EMAIL_PASS not configured in .env")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = config.EMAIL_USER
        msg["To"]      = to

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(config.EMAIL_HOST, config.EMAIL_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(config.EMAIL_USER, config.EMAIL_PASS)
            server.sendmail(config.EMAIL_USER, to, msg.as_string())

        print(f"[Email] Sent to {to} — Subject: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[Email] Authentication failed — check EMAIL_USER and EMAIL_PASS (use App Password for Gmail).")
        return False
    except smtplib.SMTPException as e:
        print(f"[Email] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[Email] Unexpected error: {e}")
        return False
