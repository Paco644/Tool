import json

import gradio as gr

from MSALApp import to_field_name, MSALApp

with open("static_data.json") as f:
    static_data = json.load(f)

systems = static_data["systems"]
activities = static_data["activities"]
extensions = static_data["extensions"]

xrmtool = MSALApp()


def notnull(value: object, message: str) -> None:
    """
    Checks if the value is not null and throws an error if it is
    :param value: Value to check
    :param message: Error message to throw
    :return: None
    """
    if not value:
        raise gr.Error(message)


notnull(xrmtool.app, "App couldn't be initialized. Missing API variables in environment!")


def get_entities(system: str) -> list[str]:
    """
    Retrieves all entities from a system
    :param system: Systemname (e.g. 'myxrm-dev01')
    :type system: str
    :return: List of all entities of the system
    """
    entities_json = xrmtool.get(system, "entities", "select=entitysetname")
    entities = [
        entity["entitysetname"]
        for entity in entities_json
        if entity["entitysetname"] not in activities
    ]
    entities.sort()
    return entities


def prepare_data(data):
    new_data = data
    del data["@odata.etag"]
    for value in data:
        if not value:
            new_data.pop(value)

    return new_data


def transfer_data(
        source_system: str,
        target_system: str,
        filter: str,
        entity: str,
        include_relation: int,
        dropdown: int,
        progress=gr.Progress(),
):
    notnull(source_system, "Please select a source system")
    notnull(entity, "Please select an entity to export")

    result = xrmtool.get(source_system, entity, filter)

    notnull(result, f"Entity {entity} did not return any data with filter {filter}")

    for value in result:
        if value[0] == "_":
            print(value)

    return gr.update(value="{}")


def process_requests(system, reqs):
    return gr.update(value="Done")


def on_entity_change():
    return gr.update(), gr.update(value="Only export response")


def on_system_change(system):
    return gr.update(choices=get_entities(system))


def on_relation_settings_change(system, choice, entity_name: str):
    if choice == 1:
        return gr.update(
            choices=[
                data["name"].split("_", 1)[1]
                for data in xrmtool.get(
                    system,
                    "relationships",
                    f"select=name&$filter=(startswith(name, '{to_field_name(entity_name)[:-2]}'))",
                )
            ],
            interactive=True,
        )
    else:
        return gr.update(interactive=False)


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    source_system = gr.Dropdown(
        label="Source system", choices=systems, value=systems[0]
    )

    tab1 = gr.Tab("Transfer using Web API")
    with tab1:
        target_system = gr.Dropdown(
            label="Target system", choices=systems, value=systems[1], interactive=True
        )

        entity = gr.Dropdown(
            get_entities(source_system.value),
            label="Selected entity",
        )

        api_filter = gr.Textbox(
            placeholder="Web API Url (Filter)",
            label="Filter",
            show_copy_button=True,
            value="top=1",
        )

        with gr.Row():
            include_relations = gr.Radio(
                ["Only export response", "Export with relations"],
                label="Relation Settings",
                info="Please use one of these options",
                type="index",
                value="Only export response",
                interactive=True,
            )

            relation_dropdown = gr.Dropdown(
                label="Relations",
                multiselect=True,
                info="All relations regarding this entity",
                interactive=False,
            )
        send_button = gr.Button("Submit")
        with gr.Row():
            reqs = gr.Json(label="Batch Request")

            final = gr.Textbox(
                placeholder="Output will be send here",
                label="Output",
                interactive=False,
            )

    tab2 = gr.Tab("Export Solution")
    with tab2:
        gr.Label("NOT IMPLEMENTED YET")

    with gr.Tab("Settings"):
        with gr.Accordion("Static Data", open=False):
            gr.Json(value=static_data)

        with gr.Accordion("Extensions", open=False):
            gr.Json(value=extensions)

    with gr.Tab("Logs"):
        gr.Textbox("Logs")

    # Listeners
    include_relations.change(
        on_relation_settings_change,
        inputs=[source_system, include_relations, entity],
        outputs=relation_dropdown,
    )

    source_system.change(on_system_change, inputs=source_system, outputs=entity)

    send_button.click(
        transfer_data,
        inputs=[
            source_system,
            target_system,
            api_filter,
            entity,
            include_relations,
            relation_dropdown,
        ],
        outputs=[reqs],
    )

    entity.change(
        on_entity_change, inputs=None, outputs=[relation_dropdown, include_relations]
    )

    reqs.change(process_requests, inputs=[target_system, reqs], outputs=[final])

demo.launch(show_error=True, server_port=8080, ssl_verify=True, enable_queue=True)
