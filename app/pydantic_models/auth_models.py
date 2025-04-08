from app.pydantic_models.clean_model import CleanableBaseModel


class TokenResponse(CleanableBaseModel):
    access_token: str
    refresh_token: str


class LoginRequest(CleanableBaseModel):
    username: str
    password: str
