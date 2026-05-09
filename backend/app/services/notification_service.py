"""
Madhyastha — Notification Service
SMTP Email notifications with graceful fallbacks

All functions are SYNCHRONOUS because smtplib is blocking I/O.
FastAPI BackgroundTasks will run them in a threadpool automatically.
"""
import logging
import smtplib
import re
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("madhyastha.notify")


def send_email(to_email: str, subject: str, body: str, attachment_path: Optional[str] = None) -> bool:
    """Send email via SMTP (Gmail) with anti-spam compliant structure.
    This is a SYNC function — BackgroundTasks runs it in a threadpool."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
        logger.info(f"[MOCK EMAIL] Body preview: {_strip_html(body)[:120]}...")
        return True
    try:
        # Root container — allows attachments
        msg = MIMEMultipart("mixed")
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = f"[Madhyastha] {subject}"

        # Alternative container — plain text + HTML (anti-spam)
        body_container = MIMEMultipart("alternative")

        # Plain text version (auto-generated from HTML)
        plain_text = _strip_html(body)
        body_container.attach(MIMEText(plain_text, "plain"))

        # HTML version with branding
        html_body = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 20px; border-radius: 12px 12px 0 0;">
                <h2 style="color: white; margin: 0;">⚖️ Madhyastha</h2>
                <p style="color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 0.85rem;">AI-Powered Dispute Resolution</p>
            </div>
            <div style="background: #ffffff; padding: 24px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px;">
                {body}
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
                <p style="font-size: 0.75rem; color: #94a3b8;">
                    This is an automated message from Madhyastha AI Dispute Resolution Platform.<br/>
                    Legal Anchors: Mediation Act 2023 | Arbitration &amp; Conciliation Act 1996
                </p>
            </div>
        </div>
        """
        body_container.attach(MIMEText(html_body, "html"))

        msg.attach(body_container)

        # Attach PDF if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "pdf")
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
                msg.attach(part)

        # Send via SMTP
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"✉ Email sent to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"✉ Email FAILED to {to_email}: {e}")
        import traceback
        traceback.print_exc()
        return False


def _strip_html(html: str) -> str:
    """Strip HTML tags to produce a plain-text version for anti-spam compliance"""
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<hr[^>]*>', '\n---\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def send_sms(phone: str, message: str) -> bool:
    """SMS placeholder — logs mock. For production, integrate Twilio or TextLocal."""
    logger.info(f"[MOCK SMS] To: {phone} | Message: {message[:80]}...")
    return True


def notify_parties(dispute, parties, subject: str, message: str):
    """Send notifications to all parties in a dispute"""
    html_message = f"<p>{message}</p>"
    for party in parties:
        if party.email:
            send_email(party.email, subject, html_message)
        if party.phone:
            send_sms(party.phone, message)


def send_dispute_link(party_name: str, email: str, role: str, link: str, dispute_title: str):
    """Send dispute session link to a party (sync — called via BackgroundTasks)"""
    body = f"""
    <h3>Hello {party_name},</h3>
    <p>You have been invited to participate in dispute resolution for:</p>
    <div style="background: #f1f5f9; padding: 16px; border-radius: 8px; margin: 16px 0;">
        <strong>{dispute_title}</strong><br/>
        <span style="color: #64748b;">Role: {role.replace('_', ' ').title()}</span>
    </div>
    <p>Click the link below to access your private mediation session:</p>
    <a href="{link}" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2);
       color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
        Join Mediation Session
    </a>
    <p style="margin-top: 16px; font-size: 0.88rem; color: #64748b;">
        This link is private and unique to you. Do not share it with the other party.
    </p>
    """
    send_email(email, f"Dispute Invitation: {dispute_title}", body)


def send_agreement_notification(party_name: str, email: str, dispute_title: str, pdf_path: Optional[str] = None):
    """Send agreement PDF to a party (sync — called via BackgroundTasks)"""
    body = f"""
    <h3>Dear {party_name},</h3>
    <p>An agreement has been finalized for your dispute:</p>
    <div style="background: #f0fff4; padding: 16px; border-radius: 8px; margin: 16px 0; border-left: 4px solid #48bb78;">
        <strong>✅ {dispute_title}</strong><br/>
        <span style="color: #2d3748;">Settlement agreement is attached as PDF.</span>
    </div>
    <p>This agreement is legally binding under <strong>Section 22, Mediation Act 2023</strong>.</p>
    """
    send_email(email, f"Agreement Finalized: {dispute_title}", body, attachment_path=pdf_path)
