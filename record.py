from misc import to_field_name, to_plural
from misc import System, Ignore
from reference import Reference


class Record:
    """
    Class wrapper for a record
    """

    def __init__(
        self, system: System, entity_name: str, original_payload: dict[str, any]
    ):
        """
        A class wrapper for a crm record.
        :param system: The system the record is currently in
        :param entity_name: The entity name of the record.
        :param original_payload: The original payload response returned from the web request.
        """
        self.system = system
        self.entity_name = entity_name
        self.original_payload = original_payload
        self.references: list[Reference] = []
        self.id = original_payload[to_field_name(entity_name)]

        new_payload = original_payload.copy()
        references = []

        new_payload.pop("@odata.etag", None)

        known_records.append(self)

        for key, value in original_payload.items():
            if not value:
                new_payload.pop(key)
                continue

            if key.startswith("_"):
                if key.endswith("lookuplogicalname"):
                    ref_entity = to_plural(value)
                    new_payload.pop(key)
                    continue

                new_payload.pop(key)

                if ref_entity in [member.value for member in Ignore]:
                    continue

                references.append(Reference(system, ref_entity, value))

        self.payload = new_payload
        self.references = references

    def already_exists(self, target_system):
        from msal_app import crm

        response = crm().get(
            target_system,
            self.entity_name,
            filter=f"filter=({to_field_name(self.entity_name)} eq {self.id})",
        )
        response_list = list(response)
        if len(response_list) == 0:
            return False

        return True

    def build_export_string(self, system: System):

        ref_obj = {}

        for ref in self.references:
            pass

        return {"payload": self.payload, "references": self.references}


def get_record(system: System, entity: str, id: str) -> Record:
    from msal_app import crm

    records = crm().get(system, entity, f"filter=({to_field_name(entity)} eq {id})")
    return records[0] if records else None


def id_in_list(id: str):
    for record in known_records:
        if record.id == id:
            return record
    else:
        return None


known_records: list[Record] = []
