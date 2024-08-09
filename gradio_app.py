import sys

import gradio as gr

import main
from misc import get_enum_values, Activity, Ignore, to_field_name
from msal_app import crm


def on_entity_change():
    return gr.update(), gr.update(value="Only export response")


def get_entities(system) -> list[str]:
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


def on_system_change(system):
    return gr.update(choices=get_entities(system))


def on_system_change_solutions(system):
    return gr.update(choices=main.get_solutions_from_system(system))


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
    def __init__(self, config):
        config = dict(config.items("Options"))

        systems = config["systems"].split(",")
        tar_system = config["defaulttargetenvironment"]
        src_system = config["defaultsourceenvironment"]
        path_to_solution = config["pathtomainsolution"]

        with gr.Blocks(theme=gr.themes.Soft()) as demo:
            source_system = gr.Dropdown(
                label="Source system",
                choices=systems,
                value=src_system,
            )

            # Tab 0
            # Export Solution

            solutions = main.get_solutions_from_system(source_system.value)

            with gr.Tab("Export Solution"):
                main_solution_path = gr.Textbox(
                    label="Path to Customizing Solution", value=path_to_solution
                )
                solution_to_export = gr.Dropdown(
                    label="Solution To Export",
                    choices=solutions,
                    value="AFDCustomizing",
                    interactive=True,
                )

                export_button = gr.Button("Export Solution")

                solution = gr.File(label="Solution Zip File", interactive=False)

                export_button.click(
                    main.export_solution,
                    inputs=[solution_to_export, main_solution_path, source_system],
                    outputs=solution,
                )

                source_system.change(
                    on_system_change_solutions,
                    inputs=[source_system],
                    outputs=solution_to_export,
                )

            # Tab 1.5
            # Transfer Solution

            with gr.Tab("Transfer Solution"):
                system_to_transfer_solution = gr.Dropdown(
                    choices=systems, label="Target System", value=tar_system
                )

                solution_to_transfer = gr.Dropdown(
                    label="Solution To Export",
                    choices=solutions,
                    value="Temp",
                    interactive=True,
                )

                publish = gr.Checkbox(label="Publish customizations after transfer", value=True)

                transfer_button = gr.Button("Transfer Solution")

                transfer_output = gr.Textbox(label="Output", interactive=False)

                transfer_button.click(main.transfer_solution,
                                      inputs=[source_system, system_to_transfer_solution, solution_to_transfer,
                                              publish], outputs=transfer_output)

                source_system.change(
                    on_system_change_solutions,
                    inputs=[source_system],
                    outputs=solution_to_transfer,
                )

            # Tab 1
            # Transfer using Web API

            with gr.Tab("Transfer using Web API"):
                target_system = gr.Dropdown(
                    label="Target system",
                    choices=systems,
                    value=tar_system,
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
                    choices=systems,
                    value=tar_system,
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
                db_choice = gr.Radio(
                    choices=["GET", "POST"],
                    type="index",
                    label="Method",
                    info="Choose one of these options",
                    value="GET",
                )
                db_payload = gr.Textbox(
                    label="Input", value=str({"name": "Franz Meitz"})
                )
                db_submit = gr.Button("Execute")
                db_output = gr.Json(label="Output")

            # Listeners
            db_submit.click(
                main.debug, inputs=[db_choice, db_payload], outputs=[db_output]
            )

            # Tab 4
            # Configuration

            settings_inputs = []

            with gr.Tab("Settings"):
                for setting in config:
                    tx = gr.Textbox(label=setting, value=config[setting], interactive=True)
                    settings_inputs.append(tx)

                settings_button = gr.Button("Save Settings")

                settings_button.click(main.save_settings, inputs=settings_inputs)

        demo.launch(show_error=True, server_port=80, ssl_verify=True)
