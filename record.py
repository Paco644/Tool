from misc import to_field_name, to_plural
from misc import System, Ignore
from reference import Reference


class Record:
    """
    Class wrapper for a record
    """

    def __init__(
            self,
            system: System,
            entity_name: str,
            original_payload: dict[str, any],
            cache_record,
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
        references = {}

        new_payload.pop("@odata.etag", None)

        if cache_record:
            known_records[self.id] = self

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

                trimmed_key = key[1:-6]

                if ref_entity in [member.value for member in Ignore] and trimmed_key != "ownerid":
                    continue

                references[value] = Reference(system, ref_entity, value, trimmed_key)

        self.payload = new_payload
        self.references = references

    def already_exists(self, target_system):
        from msal_app import crm

        response = crm().get(
            target_system,
            self.entity_name,
            filter=f"filter=({to_field_name(self.entity_name)} eq {self.id})",
        )
        return bool(list(response))


def get_record(system: System, entity: str, id: str) -> Record:
    from msal_app import crm

    records = crm().get(system, entity, f"filter=({to_field_name(entity)} eq {id})")
    return records[0] if records else None


# TODO: OPTIMIZE FUNCTION -> INPUT A LIST AND COMPARE RESULTS. THIS WILL USE ONLY ONE API CALL
# This will only work with entities that are equal
def filter_existing_records(records: list[Record], target_system) -> list[Record]:
    return records


known_records: dict[str, Record] = {}
