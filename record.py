from misc import to_field_name
from misc import System
from reference import Reference

known_ids = []


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

        for key, value in original_payload.items():
            if not value:
                new_payload.pop(key)
                continue

            if key.startswith("_"):
                trimmed_key = key[1:-6]
                references.append(Reference(system, trimmed_key, value))
                new_payload.pop(key)

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


def get_record(system: System, entity: str, id: str) -> Record:
    from msal_app import crm

    print(entity)
    records = crm().get(system, entity, f"filter=({to_field_name(entity)} eq {id})")
    return records[0] if records else None
