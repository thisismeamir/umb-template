from fastapi import APIRouter
from app.config import Settings

class HealthRouter(APIRouter):
    def __init__(self):
        super().__init__()
        self._router = APIRouter(prefix="/health", tags=["system"])

        @self._router.get("/")
        async def health():
            return {"status": "ok"}

        @self._router.get("/version")
        async def version():
            return {
                "version": Settings().api_version,
                "status": "ok"
            }

        @self._router.get("/ping")
        async def ping():
            return {"ping": "pong"}

    @property
    def router(self) -> APIRouter:
        return self._router