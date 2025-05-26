import smtplib
from email.mime.text import MIMEText

from fastapi import HTTPException
from loguru import logger

from app.config import Settings

settings = Settings()


def send_email(to_email: str, body: str):
    if (
        not settings.SMTP_PASSWORD
        or not settings.SMTP_PORT
        or not settings.SMTP_SERVER
        or not settings.SMTP_USERNAME
    ):
        raise HTTPException(
            status_code=400, detail="Неверные данные для отправки почты"
        )
    msg = MIMEText(body)
    msg["Subject"] = "Подтверждение почты"
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, int(settings.SMTP_PORT)) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [msg["To"]], msg.as_string())
            logger.info(f"Письмо отправлено на {to_email}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма на {to_email}: {e}")
        raise
