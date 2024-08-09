import json
import subprocess
from configparser import ConfigParser
import os

from gradio import update, Progress, Info
from msal_app import crm
from record import (
    known_records,
    loaded_records,
    Record,
    filter_existing_records,
    Reference,
)


def save_settings(*settings):
    for setting in settings:
        print(setting)

    Info("Settings Successfully Saved")


def transfer_solution(
        system, target_system, solution_name, publish, progress=Progress()
):
    export_solution(solution_name, "", system, progress)
    progress(.5, desc="Importing Solution...")
    # Update Progress description
    command = (
            f"pac solution import --path ./solutions/{solution_name}.zip --environment https://{target_system}.crm4.dynamics.com/ --activate-plugins"
            + (" --publish-changes" if publish else "")
    )

    process = subprocess.run(
        command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode == 0:
        return update(value=process.stdout.decode())


def traverse_record(record: Record, target_system, already_traversed=None):
    if already_traversed is None:
        already_traversed = []

    def traverse_reference(record: Record, reference: Reference, already_traversed):
        ref_rec = reference.get_record()

        # Remove the team reference because a team can not be existing in target environment
        if ref_rec.entity == "teams":
            print(ref_rec.payload, ref_rec.original_payload)
            traverse_record(ref_rec, target_system, already_traversed)

        if (
                reference.id in already_traversed
                or ref_rec.already_exists(target_system)
                or ref_rec.entity == "systemusers"
        ):
            record.payload[
                reference.key + "@odata.bind"
                ] = f"/{reference.entity}({ref_rec.id})"
            return

        record.payload[reference.key] = ref_rec.payload

        traverse_record(ref_rec, target_system, already_traversed)

    if record.id in already_traversed:
        return
    else:
        already_traversed.append(record.id)

    for ref in record.references.values():
        traverse_reference(record, ref, already_traversed)


def transfer_data(
        source_system,
        target_system,
        filter: str,
        entity: str,
        include_relations: int,
        dropdown,
        progress=Progress(),
):
    output = []

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
            output.append(obj)
            break

    known_records.update(loaded_records)

    # with open("cache.pkl", "wb") as f:
    #    print("Opened cache and saving dictionary")
    #    pickle.dump(known_records, f)

    return update(value=json.dumps(output, indent=4))


def get_solutions_from_system(system):
    command = f"pac solution list --environment https://{system}.crm4.dynamics.com/"
    print(command)
    process = subprocess.run(
        command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode == 0:
        output = process.stdout.decode()
        lines = output.split("\n")[5:-2]

        unique_names = []
        for line in lines:
            split = line.split()
            name = split[0]
            managed = split[-1] == "True"

            if not managed:
                unique_names.append(name)

        return unique_names

    return ["Could not load solutions"]


def export_solution(solution_name, export_path, environment, progress=Progress()):
    progress(0, desc="Exporting Solution...")

    solution_path = f'./solutions/{solution_name}.zip'

    command = f"pac solution export --name {solution_name} --path ./solutions --environment https://{environment}.crm4.dynamics.com/"
    print(command)
    process = subprocess.run(
        command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if process.returncode == 0:
        print(
            f"Solution {solution_name} exported successfully to {os.path.abspath(f'./solutions/{solution_name}.zip')}"
        )
        if solution_name == "AFDCustomizing":
            subprocess.run(
                f"pac solution unpack --zipfile ./solutions/{solution_name}.zip --folder {export_path}",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        return update(value=f"./solutions/{solution_name}.zip")
    else:
        print(f"Failed to export solution. Error: {process.stderr.decode()}")


def transfer_configuration_settings(
        source_system, target_system, dov, progress=Progress()
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
        return update(value=crm().post("myxrm-dev01", "accounts", input).json())


if __name__ == "__main__":
    from gradio_app import GradioApp

    # Read Config
    config = ConfigParser()
    config.read("conf.ini")

    GradioApp(config)
