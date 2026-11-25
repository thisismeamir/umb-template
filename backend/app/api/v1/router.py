from __future__ import annotations

from app.api.dependencies import Api
from app.api.v1.analytics.router import AnalyticsRouter
from app.api.v1.auth.router import AuthRouter
from app.api.v1.collections.router import CollectionRouter
from app.api.v1.entities.router import EntityRouter
from app.api.v1.export.router import ExportRouter
from app.api.v1.general.HealthRouter import HealthRouter
from app.api.v1.jobs.router import JobRouter
from app.api.v1.navigation.router import NavigationRouter
from app.api.v1.search.router import SearchRouter
from app.config import get_settings


class ApiV1(Api):
    """
    Main api class for version 1 of the api.
    Mounts all 8 domain routers + health router under /api/v1.
    """

    def __init__(self) -> None:
        self.version = "v1"
        super().__init__(version="v1", latest_version=get_settings().api_version)
        self.router.include_router(EntityRouter().router)
        self.router.include_router(NavigationRouter().router)
        self.router.include_router(SearchRouter().router)
        self.router.include_router(AnalyticsRouter().router)
        self.router.include_router(ExportRouter().router)
        self.router.include_router(AuthRouter().router)
        self.router.include_router(CollectionRouter().router)
        self.router.include_router(JobRouter().router)
        self.router.include_router(HealthRouter().router)
