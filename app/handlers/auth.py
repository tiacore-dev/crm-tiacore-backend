from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from app.config import Settings
from app.database import User


# Конфигурация JWT
settings = Settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE_DAYS = int(settings.REFRESH_TOKEN_EXPIRE_DAYS)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

bearer_scheme = HTTPBearer()


# Создание токена


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created Access JWT: {encoded_jwt}")
    return encoded_jwt

# Проверка токена


def create_refresh_token(data: dict):
    return create_access_token(data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)):
    """
    Проверяет и декодирует токен из заголовка Authorization.
    """
    token = credentials.credentials  # Достаём сам токен
    return verify_token(token)  # Проверяем токен и возвращаем username


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return username
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc


async def login_handler(username: str, password: str):
    user = await User.filter(username=username).first()

    if not user:
        return None  # Возвращаем None, если пользователь не найден

    check_password = user.check_password(password)
    if check_password:
        return user

    return None  # Возвращаем None, если пароль неверный
