from __future__ import annotations

from app.config import get_settings
from app.engine.entry.EntityEngine import EntityEngine
from app.models.entity.EntityRoute import EntityRoute
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import (
    AggregateResult,
    ApiInformation,
    DistinctResult,
    Response,
    VersionSummary,
)
from app.repositories.entry.EntityRepository import EntityRepository
from app.services.entity.EntityRequestValidatorService import EntityRequestValidator


class EntityService:
    """Orchestrates validation, SQL planning, execution, and response shaping for entity routes."""

    def __init__(self, route: EntityRoute, repository: EntityRepository) -> None:
        self._route = route
        self._repository = repository

    async def response(
        self, request: EntityRequestModel, *, randLimit: int = 1
    ) -> Response:
        apiInfo = ApiInformation(version=get_settings().api_version)
        validationResult = EntityRequestValidator(request, route=self._route).validate()

        if not validationResult.valid:
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                status="error",
            )

        engine = EntityEngine(request)

        # 1. Random endpoint
        if self._route == EntityRoute.RAND:
            plan = engine.executeRandom(limit=randLimit)
            rows = await self._repository.executeQuery(plan.sql, plan.params)
            projected = engine.applyTakeClause(rows)
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                entities=projected,
                returned=len(projected),
            )

        # 2. Version history query
        if request.versions is not None:
            plan = engine.executeVersions()
            rows = await self._repository.executeQuery(plan.sql, plan.params)
            versions = [
                VersionSummary(
                    id=str(row["id"]),
                    version=int(row["version"]),
                    createdAt=row["created_at"],
                    createdBy=str(row["created_by"]),
                    source=str(row["source"]),
                )
                for row in rows
            ]
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                versions=versions,
                returned=len(versions),
            )

        # 3. Aggregate query
        if request.aggregate is not None:
            path, plan = engine.executeAggregate()
            rows = await self._repository.executeQuery(plan.sql, plan.params)
            rawVal = rows[0]["value"] if rows else None
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                aggregate=AggregateResult(
                    fn=request.aggregate.fn.value,
                    path=path,
                    value=rawVal,
                ),
            )

        # 4. Distinct values query
        if request.distinct is not None:
            path, plan = engine.executeDistinct()
            rows = await self._repository.executeQuery(plan.sql, plan.params)
            values = [row["value"] for row in rows]
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                distinct=DistinctResult(path=path, values=values),
                returned=len(values),
            )

        # 5. Count-only query
        if request.count is True and self._route in (
            EntityRoute.ROOT,
            EntityRoute.STAT,
            EntityRoute.QUERY,
            EntityRoute.SEARCH,
        ) and request.take is None and request.get is None and request.page is None:
            plan = engine.executeCount()
            rows = await self._repository.executeQuery(plan.sql, plan.params)
            total = int(rows[0]["count"]) if rows else 0
            return Response(
                apiInformation=apiInfo,
                validationResult=validationResult,
                count=total,
                total=total,
            )

        # 6. Standard entity retrieval (ROOT, QUERY, SEARCH, GET)
        plan = engine.executeRoot()
        dbRows = await self._repository.executeQuery(plan.sql, plan.params)
        pageRows, nextCursor, hasMore = engine.applyPagination(dbRows)
        sampledRows = engine.applyGetClause(pageRows)
        finalRows = engine.applyTakeClause(sampledRows)

        return Response(
            apiInformation=apiInfo,
            validationResult=validationResult,
            entities=finalRows,
            returned=len(finalRows),
            count=len(finalRows) if request.count else None,
            nextCursor=nextCursor,
            hasMore=hasMore,
        )
