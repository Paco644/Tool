import pickle

from misc import to_field_name, to_plural
from misc import System, Ignore
from reference import Reference
from logger import logger, LoggerLevel


class Record:
    """
    Class wrapper for a record
    """

    def __init__(
        self,
        system: System,
        entity: str,
        original_payload: dict[str, any],
        cache_record,
    ):
        """
        A class wrapper for a crm record.
        :param system: The system the record is currently in
        :param entity: The entity name of the record.
        :param original_payload: The original payload response returned from the web request.
        """
        self.system = system
        self.entity = entity
        self.original_payload = original_payload
        self.references: list[Reference] = []
        self.id = original_payload[to_field_name(entity)]

        new_payload = original_payload.copy()
        references = {}

        new_payload.pop("@odata.etag", None)

        if cache_record:
            known_records[self.id] = self

        for key, value in original_payload.items():
            if not value:
                #new_payload.pop(key)
                new_payload[key] = "null"
                continue

            if key.startswith("_"):
                if key.endswith("lookuplogicalname"):
                    ref_entity = to_plural(value)
                    new_payload.pop(key)
                    continue

                new_payload.pop(key)

                trimmed_key = key[1:-6]

                if (
                    ref_entity in [member.value for member in Ignore]
                    and trimmed_key != "ownerid"
                ):
                    continue

                references[value] = Reference(system, ref_entity, value, trimmed_key)

        self.payload = new_payload
        self.references = references

    def already_exists(self, target_system):
        from msal_app import crm

        response = crm().get(
            target_system,
            self.entity,
            filter=f"filter=({to_field_name(self.entity)} eq {self.id})",
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


try:
    with open("cache.pkl", "rb") as f:
        known_records: dict[str, Record] = pickle.load(f)
        loaded_records = known_records.copy()
except EOFError:
    logger().log("Error: 'cache.pkl' is empty or contains invalid pickled data.", LoggerLevel.WARNING)
    known_records: dict[str, Record] = {}
    loaded_records = known_records.copy()

logger().log(f"Loaded {len(known_records)} records from pickle cache")
