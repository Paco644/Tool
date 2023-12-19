from requests import Response
from misc import Activity, System, Ignore, to_field_name, to_plural
from msal_app import MsalApp
from gradio import update

import gradio_app

crm = MsalApp()

def transfer_data(
    source_system: System,
    target_system: System,
    request_filter: str,
    entity: str,
    include_relation: int,
    dropdown: int,
):
    records = crm.get(source_system, entity, request_filter)

    for record in records:
        print(record.payload)

    return update(value={"test": True})


def process_requests(system, reqs):
    print("Transferring Records")
    return update(value="Done")
