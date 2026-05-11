from app.models.event.response import Event

class EventMapper:
    @staticmethod
    def to_model(row) -> Event:
        return Event.model_validate(dict(row))