from typing import Dict, List, Optional
from pydantic import BaseModel, UUID4, model_validator


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    permissions: Optional[Dict[UUID4, List[str]]] = None
    is_superadmin: bool
    user_id: UUID4

    @model_validator(mode="after")
    def check_permissions_for_non_superadmin(self) -> "TokenResponse":
        if not self.is_superadmin and not self.permissions:
            raise ValueError(
                "permissions must be provided if user is not a superadmin")
        return self


class LoginRequest(BaseModel):
    email: str
    password: str
