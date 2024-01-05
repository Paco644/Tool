from misc import System
from gradio import update
from msal_app import crm


def transfer_data(
    source_system: System,
    target_system: System,
    filter: str,
    entity: str,
    ir: int,
    dd: int,
):

    records = crm().get(source_system, entity, filter)

    data = {}

    for record in records:
        if record.already_exists(target_system):
            continue
        data[record.id] = record.build_export_string(target_system)

    return update(value=data)


def process_requests(system, records):
    print("Transferring Records")
    return update(value="Done")


if __name__ == "__main__":
    from gradio_app import GradioApp

    gradio_app = GradioApp()
