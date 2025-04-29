import smtplib
from email.mime.text import MIMEText
from loguru import logger
from app.config import Settings

settings = Settings()


def generate_verification_link(token: str) -> str:
    return f"{settings.BACK_ORIGIN}/api/auth/verify-email?token={token}"


def send_verification_email(to_email: str, token: str):
    verification_link = generate_verification_link(token)
    body = f"""
    Здравствуйте!

    Пожалуйста, подтвердите свою почту, перейдя по ссылке:
    {verification_link}

    Если это были не вы, проигнорируйте это письмо.
    """

    msg = MIMEText(body)
    msg['Subject'] = 'Подтверждение почты'
    msg['From'] = settings.SMTP_USERNAME
    msg['To'] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, 587) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg['From'], [msg['To']], msg.as_string())
            logger.info(
                f"Письмо для подтверждения почты отправлено на {to_email}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма на {to_email}: {e}")
        raise  # пробрасываем исключение выше, чтобы не скрыть ошибку
