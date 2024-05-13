import json

from misc import System
from gradio import update
from msal_app import crm
from record import known_records, Record


def merge(records: dict[str:Record], layer=0) -> dict:
    # Get all parent ids to know what exists
    parent_ids = [set()]

    for id, record in records.items():
        parent_ids[layer].add(id)

    for id, record in records.items():
        for ref in record.references:
            if ref.id in parent_ids[layer]:
                obj = ref.record.payload

                records[id].payload[ref.key] = obj

                print(record.payload)
                del records[id]
            return merge(records)

    return records


def transfer_data(
        source_system: System,
        target_system: System,
        filter: str,
        entity: str,
        include_relations: int,
        dropdown,
):
    records = crm().get(source_system, entity, filter)

    print(
        f"Loaded a total of {len(known_records.values())} unique records into cache that will be needed for transfer"
    )

    merge(data := known_records.copy())

    for key, record in data.items():
        print(record.payload)


    return update(value=data)


def process_requests(system, records):
    return update(value="Done")


if __name__ == "__main__":
    from gradio_app import GradioApp

    gradio_app = GradioApp()
