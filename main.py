import json

import gradio

from misc import System
from gradio import update, Progress
from msal_app import crm
from record import known_records, Record, filter_existing_records
from reference import Reference


def traverse_record(record: Record, already_traversed=None):
    if already_traversed is None:
        already_traversed = []

    def traverse_reference(record: Record, reference: Reference, already_traversed):
        if reference.id in already_traversed:
            record.payload[
                reference.key + "@odata.bind"
            ] = f"/{reference.entity}({reference.record.id})"
            return

        data = [].append(reference.record.payload)
        print(data)

        # record.payload[reference.key] = data
        # CHANGE THIS ASAP
        record.payload[
            reference.key + "@odata.bind"
        ] = f"/{reference.entity}({reference.record.id})"

        traverse_record(reference.record, already_traversed)

    if record.id in already_traversed:
        return
    else:
        already_traversed.append(record.id)

    print(f"Traversing record of type {record.entity_name} with id {record.id}")

    for ref in record.references.values():
        traverse_reference(record, ref, already_traversed)


def transfer_data(
    source_system: System,
    target_system: System,
    filter: str,
    entity: str,
    include_relations: int,
    dropdown,
):
    print(f"{len(known_records.values())} records in cache")

    records = crm().get(source_system, entity, filter)

    print("\nDONE GETTING ALL THE DATA\n")

    for record in records:
        traverse_record(record)

        obj = record.payload

        post = crm().post(
            target_system,
            entity,
            obj,
        )

        print(post.json())

    return update(value=json.dumps(obj, indent=4))


def process_requests(system, records):
    return update(value="Done")


def transfer_configuration_settings(
    source_system: System, target_system: System, dov, progress=Progress()
):
    entity = "afd_configurationsettings"

    results = []
    records = crm().get(source_system, entity)

    # FILTER
    for record in progress.tqdm(
        filter_existing_records(records, target_system),
        "Transferring configuration settings...",
        unit="Configuration settings",
    ):
        # TODO REMOVE THIS WHEN FUNCTION IS OPTIMIZED
        if record.already_exists(target_system):
            continue

        results.append(crm().post(target_system, entity, record.payload))

    return update(value=results)


def debug(choice, input):
    if choice == 0:
        raise NotImplementedError("Operation not yet supported")
    elif choice == 1:
        print()
        return update(value=crm().post(System.DEV01.value, "accounts", input).json())


if __name__ == "__main__":
    from gradio_app import GradioApp

    gradio_app = GradioApp()
