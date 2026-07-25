# =============================================================================
# backend/services/email_service.py
#
# Async service for dispatching email notifications.
# =============================================================================

import os
import logging
from email.message import EmailMessage
import aiosmtplib

log = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025)) # Default to MailHog/Mailpit for dev
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

async def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email asynchronously.
    Falls back to console logging if the SMTP server is unreachable (useful for MVP/Dev).
    """
    msg = EmailMessage()
    msg["From"] = "no-reply@autonomous-data-scientist.com"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    
    try:
        if SMTP_HOST == "localhost" and not SMTP_USER:
            # We are likely in dev without a mail server running, just log it.
            log.info(f"--- MOCK EMAIL ---")
            log.info(f"To: {to_email}")
            log.info(f"Subject: {subject}")
            log.info(f"Body:\n{body}")
            log.info(f"------------------")
            return True
            
        await aiosmtplib.send(
            msg,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASS,
            use_tls=SMTP_PORT == 465,
            start_tls=SMTP_PORT == 587,
        )
        log.info(f"Successfully sent email to {to_email}")
        return True
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {str(e)}")
        return False
