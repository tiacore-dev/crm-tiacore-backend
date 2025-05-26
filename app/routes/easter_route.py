import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

easter_router = APIRouter()


@easter_router.get("/teapot", summary="Чайник")
async def teapot_check():
    file_path = "app/static/images/418.jpg"
    if not os.path.exists(file_path):
        return {"error": "image vanished into sorrow"}

    return FileResponse(
        path=file_path,
        media_type="image/png",
        status_code=418,  # 💥 вот оно, волшебство
    )
