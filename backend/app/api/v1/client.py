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
from fastapi import APIRouter

from app.api.routerProvider import RouterProvider


class ClientRouter:
    def __init__(self):
        self._router = APIRouter()
        self._router.add_api_route("/health", self.health, methods=["GET"])
        self._router.add_api_route("/", self.info, methods=["GET"])
    @property
    def router (self) -> APIRouter:
        return self._router

    # Returns the health of the api and server (later on though)
    def health(self) -> dict:
        return {
            "application": "fcc-physics-events",
            "api-type": "client",
            "status": "ok",
            "version": "v1"
        }

    def info(self) -> dict:
        return {
            "application": "fcc-physics-events",
            "api-type": "client",
            "status": "ok",
            "api-version": "v1",
            "number-of-events": 2, # TODO: This is a placeholder and needs to be changed.
            "last-updated": "2021-08-01T00:00:00Z"
        }