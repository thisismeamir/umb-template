from app.api.dependencies import Api
from app.config import Settings
from app.routers import entities_router


class ApiV1(Api):
    """
    Main api class for version 1 of the api.
    This module mounts all the routes in this version of the api.
    """
    def __init__(self):
        self.version = "v1"
        super().__init__(version="v1", latest_version=Settings().api_version)
        self.router.include_router(entities_router.router)
