import csv
import io
import json

import yaml
from typing import List
from app.models.event.query import EventQuery, EventFields
from app.utils.type_coerce import coerce_value


class EventQueryBuilder:
    """
    Event Query Builder is a transformation layer between the queries received from clients (web, applications, etc.)
    and the internal backend modules, it makes sure that given a query of some sort we can have an EventQuery object.
    This ensures safety, and composability of the software.
    """
    _allowed_fields = set(EventFields.model_fields.keys())

    @staticmethod
    def from_dict(event_dict: dict[str,str]) -> EventQuery:
        """
        Transform a dictionary into an Event Query object.
        :param event_dict:
        :return: EventQuery
        """
        field_data = {}

        for key, value in event_dict.items():
            if key not in EventFields.model_fields:
                continue

            field_info = EventFields.model_fields[key]
            expected_type = field_info.annotation

            coerced = coerce_value(expected_type, value)

            # silently drop invalid values
            if coerced is None:
                continue

            field_data[key] = coerced

        return EventQuery(fields=EventFields(**field_data))

    @staticmethod
    def from_list(event_list: list[str], separator: str) -> EventQuery:
        """
        Transform a list into an Event Query object.
        Assuming that the list is of strings with <field-key><separator><field-unary> type.
        We make a dictionary out of it and then pass to from_dict function.
        :param separator:
        :param event_list:
        :return: EventQuery
        """
        event_dict = {}
        for item in event_list:
            item = item.split(separator)
            if len(item) == 2:
                item_key = item[0].strip()
                item_value = item[1].strip()
                event_dict[item_key] = item_value
            else:
                # TODO: Should we be restricted?
                continue
        return EventQueryBuilder.from_dict(event_dict)



    @staticmethod
    def from_string(event_string: str, item_separator: str, fields_separator: str) -> EventQuery:
        """
        Transform a string into an Event Query object.
        :param event_string:
        :param item_separator:
        :param fields_separator:
        :return: EventQuery
        """
        event_string = event_string.strip().split(item_separator)
        return EventQueryBuilder.from_list(event_string, fields_separator)

    @staticmethod
    def from_json_file(event_json_file: str) -> EventQuery:
        """
        Transform a JSON file into an Event Query object.
        :param event_json_file:
        :return: EventQuery
        """
        event_dict = {}
        with open(event_json_file) as json_file:
            event_dict = json.load(json_file)
            json_file.close()
        return EventQueryBuilder.from_dict(event_dict)

    @staticmethod
    def from_json(event_json: str) -> EventQuery:
        """
        Transform a string that is JSON structure into an Event Query object.
        :param event_json:
        :return: EventQuery
        """
        return EventQueryBuilder.from_dict(json.loads(event_json))

    @staticmethod
    def from_yaml_file(event_yaml_file: str) -> EventQuery:
        """
        Transform a YAML file into an Event Query object.
        :param event_yaml_file:
        :return: EventQuery
        """
        with open(event_yaml_file) as yaml_file:
            event_dict = yaml.safe_load(yaml_file)
            yaml_file.close()
        return EventQueryBuilder.from_dict(event_dict)

    @staticmethod
    def from_yaml(event_yaml: str) -> EventQuery:
        """
        Transform a YAML string into an Event Query object.
        :param event_yaml:
        :return: EventQuery
        """
        return EventQueryBuilder.from_dict(yaml.safe_load(event_yaml))

    @staticmethod
    def from_csv_file(event_csv_file: str) -> List[EventQuery]:
        """
        A CSV file with each entry a query
        We turn each entry into a dictionary where the key is the column name.
        and then pass each to from_dict function.
        :param event_csv_file:
        :return: List[EventQuery]
        """
        event_list = []
        with open(event_csv_file) as csv_file:
            lists = csv.reader(csv_file, delimiter=',')
            header = lists[0]
            rows = lists[1:]
            for row in rows:
                event_dict = {}
                for index, column in enumerate(header):
                    event_dict[column] = row[index]
                entry = EventQueryBuilder.from_dict(event_dict)
                event_list.append(entry)
            csv_file.close()
        return event_list
