from misc import System
from gradio import update
from msal_app import crm
from record import get_record


def transfer_data(
    source_system: System,
    target_system: System,
    filter: str,
    entity: str,
    ir: int,
    dd: int,
):
    record = crm().get(source_system, entity, filter)[0]

    return update(value={"test": True})


def process_requests(system, reqs):
    print("Transferring Records")
    return update(value="Done")


if __name__ == "__main__":
    from gradio_app import GradioApp
    gradio_app = GradioApp()
