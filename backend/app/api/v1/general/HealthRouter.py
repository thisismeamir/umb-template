from fastapi import APIRouter
from app.config import Settings, get_settings
from app.models.response.response import ApiInformation, Response, ValidationResult

class HealthRouter(APIRouter):
    def __init__(self):
        super().__init__()
        self._router = APIRouter(prefix="/check", tags=["system"])
        self._settings = get_settings()
        self.apiinfo = ApiInformation(version=self._settings.api_version)
        @self._router.get("/")
        async def health():
            return Response(
            apiInformation=self.apiinfo,
            validationResult=ValidationResult()
            )

    @property
    def router(self) -> APIRouter:
        return self._router
