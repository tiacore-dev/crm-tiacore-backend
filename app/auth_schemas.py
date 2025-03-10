from fastapi.security import OAuth2PasswordBearer, HTTPBearer

# OAuth2 схема для получения токена через /auth/token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# HTTP Bearer схема для авторизации через заголовки
bearer_scheme = HTTPBearer(auto_error=False)
