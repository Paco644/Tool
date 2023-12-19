from requests import Response
from misc import Activity, System, Ignore, to_field_name, to_plural
from msal_app import App
from gradio import update

import gradio_app

crm = App()


def transfer_data(
    source_system: System,
    target_system: System,
    filter: str,
    entity: str,
    include_relation: int,
    dropdown: int,
):
    records = crm.get(target_system, entity, filter)

    for record in records:
        print(record.references)

    return update(value={"test": True})


def process_requests(system, reqs):
    print("Transferring Records")
    return update(value="Done")
