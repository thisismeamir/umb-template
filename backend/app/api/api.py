# -----------------------------------------------------------------------------
#  FCC-Physics-Event : API Version 1
#
#  Copyright (c) 2026 CERN
#
#  This file is part of the FCC-Physics-Event project and is licensed under
#  the Apache License, Version 2.0.
#  You may obtain a copy of the License at:
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#  Developer: Kid A
#
#  Contact:
#    Mattermost : amirhoss
#    Email      : amir.ebh@cern.ch
#                 kid.a@cern.ch
#                 thisismeamir@outlook.com
#    GitHub     : https://github.com/thisismeamir
# -----------------------------------------------------------------------------
from typing import Iterable, Optional

from fastapi import APIRouter, FastAPI
from fastapi.params import Depends
from starlette.types import ASGIApp

from app.api.routerProvider import RouterProvider


class Api:
    """

    """

    def __init__(self,
                 version: str = "v1",
                 prefix: str = "/api",
                 dependencies: Optional[Iterable[Depends]] = None,
                 deprecated: bool = False,
                 latest: bool = False) -> None:
        self.version: str = version
        self.prefix: str = prefix + f"/{version}"
        self.dependencies: Optional[Iterable[Depends]] = dependencies
        self.deprecated: bool = deprecated
        self.isLatest: bool = latest

        self._router: APIRouter = APIRouter(
            prefix=self.prefix,
            dependencies=list(dependencies or []),
            deprecated=deprecated,
        )

        self._mounted: bool = False

    @property
    def router(self) -> APIRouter:
        return self._router

    def include(self, provider: RouterProvider) -> None:
        if self._mounted:
            raise RuntimeError("Cannot include routers after mounting")
        self._router.include_router(provider.router)

    def include_raw(
            self,
            router: APIRouter,
            *,
            prefix: str = "",
            tags: Optional[list[str]] = None,
    ) -> None:
        if self._mounted:
            raise RuntimeError("Cannot include routers after mounting")

        self._router.include_router(router, prefix=prefix, tags=tags)

    def mount(self, app: FastAPI) -> None:
        if self._mounted:
            raise RuntimeError("API already mounted")

        app.include_router(self._router)
        self._mounted = True

    def as_subapp(self) -> ASGIApp:
        sub = FastAPI(title=f"API {self.version}")
        sub.include_router(self._router)
        return sub
