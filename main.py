import json
import pickle

from misc import System
from gradio import update, Progress
from msal_app import crm
from record import known_records, loaded_records, Record, filter_existing_records
from reference import Reference


def traverse_record(record: Record, target_system: System, already_traversed=None):
    if already_traversed is None:
        already_traversed = []

    def traverse_reference(record: Record, reference: Reference, already_traversed):
        if reference.id in already_traversed or reference.record.already_exists(
            target_system
        ):
            print(
                f"{reference.entity} with id {reference.id} already exists in {target_system}, binding id to key..."
            )
            record.payload[
                reference.key + "@odata.bind"
            ] = f"/{reference.entity}({reference.record.id})"
            return

        record.payload[reference.key] = reference.record.payload

        traverse_record(reference.record, target_system, already_traversed)

    if record.id in already_traversed:
        return
    else:
        already_traversed.append(record.id)

    print(f"Traversing record of type {record.entity} with id {record.id}")

    for ref in record.references.values():
        traverse_reference(record, ref, already_traversed)


def transfer_data(
    source_system: System,
    target_system: System,
    filter: str,
    entity: str,
    include_relations: int,
    dropdown,
    progress=Progress(),
):
    print("Starting Transfer...")

    records = crm().get(source_system, entity, filter)

    print(f"Executing transfer with {len(known_records.values())} records in cache")

    obj = {"message": "No Data was transferred"}

    for record in progress.tqdm(records, desc="Posting records...", unit="Record"):
        if record.already_exists(target_system):
            print(
                f"{record.entity} with id {record.id} already exists in {target_system}, skipping..."
            )
            continue

        traverse_record(record, target_system)

        obj = record.payload

        print(
            f"Traversed {record.entity} with id {record.id}. Attempting to post to {target_system}..."
        )

        while True:
            post = crm().post(
                target_system,
                entity,
                obj,
            )

            # TODO ERROR HANDLING
            # Check message and fix the error
            message_json = post.json()
            print(message_json)
            break

    known_records.update(loaded_records)

    with open("cache.pkl", "wb") as f:
        print("Opened cache and saving dictionary")
        pickle.dump(known_records, f)

    return update(value=json.dumps(obj, indent=4))


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
        return update(value=crm().post(System.DEV01.value, "accounts", input).json())


if __name__ == "__main__":
    from gradio_app import GradioApp

    gradio_app = GradioApp()
