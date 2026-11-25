from __future__ import annotations

from app.models.entity.EntityRoute import EntityRoute
from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import ValidationResult
from app.utility.PathTreeToList import pathTreeToList


class EntityRequestValidator:
    """Validates semantic constraints on EntityRequestModel before SQL planning."""

    def __init__(
        self, request: EntityRequestModel, route: EntityRoute = EntityRoute.ROOT
    ) -> None:
        self.request = request
        self.route = route
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        if self.route == EntityRoute.RAND:
            return self.validateRand()

        self.checkEmpty()
        self.checkRouteRequirements()
        self.checkContainsOnly()
        self.checkIdExclusivity()
        self.checkVersionsRequiresId()
        self.checkVersionVsVersions()
        self.checkSinglePathClauses()
        self.checkSortWithRandom()
        self.checkPageRequiresOrder()
        return self.result

    def validateRand(self) -> ValidationResult:
        return self.result

    def checkEmpty(self) -> None:
        if not self.request.model_fields_set:
            self.result.reject("Request is empty — at least one clause is required")

    def checkRouteRequirements(self) -> None:
        if self.route == EntityRoute.SEARCH and self.request.search is None:
            self.result.reject("/search requires a 'search' clause")
        if self.route == EntityRoute.STAT and not any(
            getattr(self.request, field) is not None
            for field in ("aggregate", "distinct", "count")
        ):
            self.result.reject(
                "/stat requires at least one of 'aggregate', 'distinct', or 'count'"
            )

    def checkContainsOnly(self) -> None:
        if (
            "contains" in self.request.model_fields_set
            and len(self.request.model_fields_set) == 1
        ):
            self.result.warn(
                "Request contains only a 'contains' clause — this is a full scan filtered by key existence and may be resource intensive"
            )

    def checkIdExclusivity(self) -> None:
        if "id" not in self.request.model_fields_set:
            return
        redundant = {"entry_type", "where", "contains", "without", "search"}
        found = sorted(redundant & self.request.model_fields_set)
        if found:
            self.result.reject(
                f"When 'id' is specified, the following clauses are redundant: {', '.join(found)}"
            )

    def checkVersionsRequiresId(self) -> None:
        if (
            "versions" in self.request.model_fields_set
            and "id" not in self.request.model_fields_set
        ):
            self.result.reject("'versions' requires 'id' to be specified")

    def checkVersionVsVersions(self) -> None:
        if (
            self.request.version is not None
            and self.request.versions is not None
        ):
            self.result.reject("Cannot specify both 'version' and 'versions'")

    def checkSinglePathClauses(self) -> None:
        if self.request.sort is not None and len(pathTreeToList(self.request.sort.by)) != 1:
            self.result.reject("'sort.by' must specify exactly one metadata path")
        if (
            self.request.aggregate is not None
            and len(pathTreeToList(self.request.aggregate.by)) != 1
        ):
            self.result.reject("'aggregate.by' must specify exactly one metadata path")
        if (
            self.request.distinct is not None
            and len(pathTreeToList(self.request.distinct)) != 1
        ):
            self.result.reject("'distinct' must specify exactly one metadata path")

    def checkPageRequiresOrder(self) -> None:
        if (
            "page" in self.request.model_fields_set
            and "sort" not in self.request.model_fields_set
        ):
            self.result.warn(
                "'page' without 'sort' produces non-deterministic pagination — consider adding a sort clause"
            )

    def checkSortWithRandom(self) -> None:
        if (
            "sort" in self.request.model_fields_set
            and self.request.get is not None
            and self.request.get.random is not None
        ):
            self.result.warn(
                "'sort' has no effect when 'get.random' is used — random sampling ignores order"
            )
