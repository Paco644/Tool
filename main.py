import configparser
import json
import logging

import gradio as gr
from requests import Response

import MSALApp

with open("static_data.json") as f:
    static_data = json.load(f)

systems = static_data["systems"]
activities = static_data["activities"]
extensions = static_data["extensions"]
mappings = static_data["mappings"]
ignore = static_data["ignore"]
relationships = static_data["relationships"]


def notnull(value: object, message: str) -> None:
    """
    Checks if the value is not null and throws an error if it is
    :param value: Value to check
    :param message: Error message to throw
    :return: None
    """
    if not value:
        raise gr.Error(message)


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
    new_data = data.copy()
    references = []
    del new_data["@odata.etag"]
    for key in data:
        value = data[key]

        if not value:
            new_data.pop(key)
            continue

        if key[0] == "_":
            trimmed_key = key[1:-6]
            references.append([trimmed_key, value])
            new_data.pop(key)

    return new_data, references


def already_exists(target_system, entity, id):
    response = xrmtool.get(
        target_system,
        entity,
        filter=f"filter=({MSALApp.to_field_name(entity)} eq {id})",
    )
    response_list = list(response)
    if len(response_list) == 0:
        return False

    return True


def response_is_error(response: Response):
    try:
        return response.json()["error"]
    except KeyError:
        return None


def search_dictionary(dictionary: dict, search: str):
    """
    Searches a dictionary and returns the key of the value
    :param dictionary: The dictionary to search in
    :param search: The Value to search in the dictionary
    :return: The key of the value
    """
    for key, value in dictionary.items():
        if value == search:
            return key
    return None


def transfer_data(
    source_system: str,
    target_system: str,
    filter: str,
    entity: str,
    include_relation: int,
    dropdown: int,
    posts=None,
    processed_ids=None,
    progress=gr.Progress(),
):
    if processed_ids is None:
        processed_ids = set()
    if posts is None:
        posts = []
    notnull(source_system, "Please select a source system")
    notnull(entity, "Please select an entity to export")

    response = xrmtool.get(source_system, entity, filter)

    notnull(response, f"Entity {entity} did not return any data with filter {filter}")

    for res in progress.tqdm(response, f"Processing {entity.lower()}", unit="Entities"):
        id = res[MSALApp.to_field_name(entity)]

        if entity in ignore or entity in activities:
            continue

        if id in processed_ids:
            continue

        if already_exists(target_system, entity, id):
            continue

        prepared_data = prepare_data(res)
        payload = prepared_data[0]
        references = prepared_data[1]

        obj = {"id": id, "entity": entity, "payload": payload}
        posts.append(obj)

        for reference in progress.tqdm(
            references,
            desc="Processing relations...",
            unit="Relations",
        ):
            referencing_field = reference[0]
            referencing_entity: str = extensions[reference[0]]
            referencing_entity_id: str = reference[1]

            if referencing_entity in ignore or referencing_entity in activities:
                continue

            if referencing_entity_id in processed_ids:
                continue

            reference_response = xrmtool.get(
                source_system,
                referencing_entity,
                f"filter=({MSALApp.to_field_name(referencing_entity)} eq {referencing_entity_id})",
            )

            reference_prepared_data = prepare_data(reference_response[0])
            reference_payload = reference_prepared_data[0]

            payload[referencing_field] = reference_payload

            processed_ids.add(referencing_entity_id)
            posts.append(obj)

            transfer_data(
                source_system,
                target_system,
                f"filter=({MSALApp.to_field_name(referencing_entity)} eq {referencing_entity_id})",
                referencing_entity,
                include_relation,
                dropdown,
                posts,
                processed_ids,
                progress,
            )
        processed_ids.add(id)
    return gr.update(value=posts)


def search_nested_dict(dictionary, target_value, parent=None):
    for key, value in dictionary.items():
        if value == target_value:
            return parent
        elif isinstance(value, dict):
            result = search_nested_dict(value, target_value, parent=key)
            if result is not None:
                return result
    return None


def process_requests(system, reqs, progress=gr.Progress()):
    for request in progress.tqdm(reqs, "Posting Entities...", unit="Entities"):
        id = request["id"]
        entity = request["entity"]
        payload: dict = request["payload"]

        while error := response_is_error(
            response := xrmtool.post(system, entity, payload)
        ):
            error_code: str = error["code"]
            error_message: str = error["message"]

            print(error_code, error_message)

            if error_code == "0x80040237":
                break

            # Some Entity in the Request does not exist in the target system
            if error_code == "0x80040217":
                entity = MSALApp.to_plural(error_message.split("'")[1])
                print(error_message, "| Skipping this request:", request)
                break

            if error_code == "0x80048408":
                search_for = error_message.split("Id ")[1][:-1]
                parent_object = search_nested_dict(payload, search_for)
                statuscode = payload[parent_object]["statuscode"]
                statecode = payload[parent_object]["statecode"]

                del payload[parent_object]["statuscode"]
                del payload[parent_object]["statecode"]

                print(
                    f"https://myxrm-dev01.crm4.dynamics.com/main.aspx?appid=34c967dc-a13a-ea11-a812-000d3a4a1f5d&pagetype=entityrecord&etn={entity}&id={id}",
                    statecode,
                    statuscode,
                )
                continue

        print(response)
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
                    f"select=name&$filter=(startswith(name, '{MSALApp.to_field_name(entity_name)[:-2]}'))",
                )
            ],
            interactive=True,
        )
    else:
        return gr.update(interactive=False)


xrmtool = MSALApp.App()

notnull(
    xrmtool.app, "App couldn't be initialized. Missing API variables in environment!"
)

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

demo.launch(show_error=True, server_port=80, ssl_verify=True, enable_queue=True)
