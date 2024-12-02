from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException, status
from typing import Optional
import aiosmtplib
from src.config import settings


async def send_email(message: str, target_email: str, subject: Optional[str] = None):
    # Create Email
    msg = MIMEMultipart()
    msg["From"] = settings.email_address
    msg["To"] = target_email
    msg["Subject"] = subject if subject else "No Subject"
    msg.attach(MIMEText(message, "plain"))

    # Send Email
    try:
        await aiosmtplib.send(
            message=msg,
            hostname="smtp.gmail.com",
            port=587,
            username=settings.email_address,
            password=settings.email_password,
            start_tls=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}",
        )
