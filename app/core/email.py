"""
Email sending module using Brevo SMTP.
"""
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str, html: bool = False) -> None:
    """
    Send an email using Brevo SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: Whether the body is HTML (default: False for plain text)
    """
    if not settings.BREVO_API_KEY:
        raise ValueError("BREVO_API_KEY is not configured")

    if not settings.BREVO_FROM_EMAIL:
        raise ValueError("BREVO_FROM_EMAIL is not configured")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = f"{settings.BREVO_FROM_NAME} <{settings.BREVO_FROM_EMAIL}>" if settings.BREVO_FROM_NAME else settings.BREVO_FROM_EMAIL
    msg['To'] = to
    msg['Subject'] = subject

    # Attach body
    if html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    # Send via SMTP using aiosmtplib for true async
    import aiosmtplib
    try:
        smtp = aiosmtplib.SMTP(hostname='smtp-relay.brevo.com', port=587, start_tls=True)
        await smtp.connect()
        # Use Brevo SMTP login as username, API key as password
        await smtp.login(settings.BREVO_SMTP_LOGIN, settings.BREVO_API_KEY)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info(f"Email sent successfully to {to}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise