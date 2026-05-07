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

from app.api.api import Api
from app.api.v1.client import ClientRouter


class ApiV1(Api):
    def __init__(self) :
        self.version = "v1"
        super().__init__(version= "v1", latest= True)
        # including routers of v1:
        # client router (used for fccanalyses and third-party implementations)
        self.include(ClientRouter())
        # server router (used for calls to update or import new stuff, mostly for dirac and rucio)
