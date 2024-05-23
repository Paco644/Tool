import sys

import gradio as gr

import main
from misc import System, get_enum_values, Activity, Ignore, to_field_name
from msal_app import crm


def on_entity_change():
    return gr.update(), gr.update(value="Only export response")


def get_entities(system: System) -> list[str]:
    """
    Retrieves all entities from a system
    :param system: Systemname (e.g. 'myxrm-dev01')
    :type system: str
    :return: List of all entities of the system
    """

    local_ignore = [*get_enum_values(Activity), *get_enum_values(Ignore)]

    entities_json = crm().get(system, "entities", "select=entitysetname", False)
    entities = [
        entity.payload["entitysetname"]
        for entity in entities_json
        if entity.payload["entitysetname"] not in local_ignore
    ]
    entities.sort()

    return entities


def on_system_change(system: System):
    return gr.update(choices=get_entities(system))


def on_relation_settings_change(system, choice, entity_name: str):
    if choice == 1:
        return gr.update(
            choices=[
                data.payload["name"].split("_", 1)[1]
                for data in crm().get(
                    system,
                    "relationships",
                    f"select=name&$filter=(startswith(name, '{to_field_name(entity_name)[:-2]}'))",
                    False,
                )
            ],
            interactive=True,
        )
    else:
        return gr.update(interactive=False)


class GradioApp:
    def __init__(self):
        with gr.Blocks(theme=gr.themes.Soft()) as demo:
            source_system = gr.Dropdown(
                label="Source system",
                choices=get_enum_values(System),
                value=System.PROD.value,
            )

            # Tab 1
            # Transfer using Web API

            tab1 = gr.Tab("Transfer using Web API")
            with tab1:
                target_system = gr.Dropdown(
                    label="Target system",
                    choices=get_enum_values(System),
                    value=System.DEV01.value,
                    interactive=True,
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
                    web_api_output = gr.Json(label="JSON Data")

            # Listeners
            include_relations.change(
                on_relation_settings_change,
                inputs=[source_system, include_relations, entity],
                outputs=relation_dropdown,
            )

            source_system.change(on_system_change, inputs=source_system, outputs=entity)

            send_button.click(
                main.transfer_data,
                inputs=[
                    source_system,
                    target_system,
                    api_filter,
                    entity,
                    include_relations,
                    relation_dropdown,
                ],
                outputs=[web_api_output],
            )

            entity.change(
                on_entity_change,
                inputs=None,
                outputs=[relation_dropdown, include_relations],
            )

            # Tab 2
            # Transfer configuration settings

            with gr.Tab("Transfer configuration settings"):
                target_system_tcs = gr.Dropdown(
                    label="Target system",
                    choices=get_enum_values(System),
                    value=System.DEV01.value,
                    interactive=True,
                )

                dov = gr.Checkbox(label="Delete old values")

                tcs_button = gr.Button("Transfer settings...")
                tcs_output = gr.Textbox(label="Output data")

            # Listeners
            tcs_button.click(
                main.transfer_configuration_settings,
                inputs=[source_system, target_system_tcs, dov],
                outputs=[tcs_output],
            )

            # Tab 3
            # Debug

            with gr.Tab("Debug"):
                db_choice = gr.Radio(choices=["GET", "POST"], type="index", label="Method",
                                     info="Choose one of these options", value="GET")
                db_payload = gr.Textbox(label="Input", value=str({'name': 'Franz Meitz'}))
                db_submit = gr.Button("Execute")
                db_output = gr.Json(label="Output")

            # Listeners
            db_submit.click(main.debug, inputs=[db_choice, db_payload], outputs=[db_output])

        demo.launch(show_error=True, server_port=80, ssl_verify=True)
