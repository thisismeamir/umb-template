from app.models.entry.EntryBaseModel import EntryBaseModel


class EntryModel(EntryBaseModel):
    metadata:  dict
    metadataSource: dict
