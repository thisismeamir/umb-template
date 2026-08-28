from app.models.request.EntityRequestModel import EntityRequestModel
from app.models.response.response import ValidationResult


class EntityRequestValidator:
    def __init__(self, request: EntityRequestModel) -> None:
        self.request = request
        self.result = ValidationResult()

    def validate(self) -> ValidationResult:
        self.checkEmpty()
        self.checkContainsOnly()
        self.checkIdExclusivity()
        self.checkVersionsRequiresId()
        self.checkSortWithRandom()
        self.checkPageRequiresOrder()
        return self.result
    def validateRand(self) -> ValidationResult:
        return self.result

    def checkEmpty(self) -> None:
        if not self.request.model_fields_set:
            self.result.reject("Request is empty — at least one clause is required")

    def checkContainsOnly(self) -> None:
        if (
                "contains" in self.request.model_fields_set
                and len(self.request.model_fields_set) == 1
        ):
            self.result.warn(
                "Request contains only a 'contains' clause — this is a full scan filtered by key existence and may be resource intensive")

    def checkIdExclusivity(self) -> None:
        if "id" not in self.request.model_fields_set:
            return
        redundant = {"entry_type", "where", "contains", "without", "search"}
        found = redundant & self.request.model_fields_set
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
                and "get" in self.request.model_fields_set
                and self.request.get.random is not None
        ):
            self.result.warn(
                "'sort' has no effect when 'get.random' is used — random sampling ignores order"
            )
