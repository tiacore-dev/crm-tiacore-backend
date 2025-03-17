from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str
