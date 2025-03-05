from fastapi import APIRouter, Form
from app.handlers import login_handler
auth_router = APIRouter()


@auth_router.post("/token")
async def login(username: str = Form(...), password: str = Form(...)):
    return await login_handler(username, password)
