from email.mime.text import MIMEText

from aiosmtplib import SMTP
from fastapi import HTTPException
from loguru import logger

from app.config import Settings

settings = Settings()


async def send_email(to_email: str, body: str):
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
        smtp = SMTP(
            hostname=settings.SMTP_SERVER,
            port=int(settings.SMTP_PORT),
            start_tls=True,
            timeout=10,
        )
        logger.info("🔌 Подключение к SMTP...")
        await smtp.connect()
        logger.info("✅ SMTP подключен")
        await smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        await smtp.send_message(msg)
        await smtp.quit()
        logger.info(f"Письмо отправлено на {to_email}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма на {to_email}: {e}")
        raise
