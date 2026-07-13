from app.config import Settings
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import Response, ApiInformation
from app.models.entity.EntityRoute import EntityRoute
from app.services.entity.EntityRequestValidatorService import EntityRequestValidator


class EntityService:
    def __init__(self, route: EntityRoute) -> None:
        self._route = route

    async def response(self, request: EntityRequestModel) -> Response:
        apiInfo = ApiInformation(version=Settings().api_version)
        validationResult = EntityRequestValidator(request).validate()

        if not validationResult.valid:
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult
            )

        match self._route:
            case EntityRoute.ROOT:
                return await self._handleRoot(apiInfo, validationResult)
            case EntityRoute.QUERY:
                return await self._handleQuery(request, apiInfo, validationResult)
            case EntityRoute.SEARCH:
                return await self._handleSearch(request, apiInfo, validationResult)
            case EntityRoute.STAT:
                return await self._handleStat(request, apiInfo, validationResult)
            case EntityRoute.HIST:
                return await self._handleHist(request, apiInfo, validationResult)

    async def _handleRoot(self, apiInfo, validationResult) -> Response:
        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult
        )

    async def _handleQuery(self, request, apiInfo, validationResult) -> Response:
        # engine.executeQuery()
        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult
        )

    async def _handleSearch(self, request, apiInfo, validationResult) -> Response:
        # engine.executeSearch()
        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult
        )

    async def _handleStat(self, request, apiInfo, validationResult) -> Response:
        # engine.executeStatistics()
        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult
        )

    async def _handleHist(self, request, apiInfo, validationResult) -> Response:
        # engine.executeHistory()
        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult
        )


