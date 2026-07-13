from dataclasses import dataclass

from app.models.request.EntityRequestModel import EntityRequestModel



@dataclass
class SQLFragment:
    sql: str
    params: list

class SQLWizard:
    """
    Given a request, transforms it into an SQLPlan object
    """
    def __init__(self, request: EntityRequestModel) -> None:
        self.request = request

    def generate(self):
        """
        generates the complete SQLPlan object.
        :return:
        """
        self.getContains()
        # self.getWithout()
        # self.getWhere()
        # self.sort()
        # self.aggregate()
        # self.count()

    def getContains(self) -> None:
        # self.rawContainsStatement = self.request.contains
        pass
