from app.config import Settings, get_settings
from app.engine.entry.EntityEngine import EntityEngine
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import Response, ApiInformation, ValidationResult
from app.models.entity.EntityRoute import EntityRoute
from app.repositories.entry.EntityRepository import EntityRepository
from app.services.entity.EntityRequestValidatorService import EntityRequestValidator

class EntityService:
    def __init__(self, route: EntityRoute, repository: EntityRepository) -> None:
        self._route = route
        self._repository = repository


    async def response(self, request: EntityRequestModel) -> Response:
        apiInfo = ApiInformation(version=get_settings().api_version)

        validationResult = EntityRequestValidator(request).validate()

        if not validationResult.valid:
            return Response(apiInformation=apiInfo, validationResult=validationResult)
        if self._route == EntityRoute.ROOT:
            if request is not None:
                self._engine = EntityEngine(request)
                plan = self._engine.executeRoot()
                dbResponse = await self._repository.executeQuery(plan.sql, plan.params)
                finalResponse = self._engine.applyGetClause(dbResponse)
                if request.count:
                    count = finalResponse.__len__()
                else:
                    count = None
                return Response(
                    apiInformation=apiInfo,
                    validationResult=validationResult,
                    entities= finalResponse,
                    count= count,
                    returned= True,
                )
            else:
                return Response(
                    apiInformation=apiInfo,
                    validationResult=validationResult
                )
        return Response(
            apiInformation= apiInfo,
            validationResult= validationResult
        )
