from enum import Enum
from gradio import Error
from requests import Response

from pattern.text.en import singularize, pluralize


class Entity(Enum):
    pass


class Activity(Entity):
    EMAILS = "emails"
    TASKS = "tasks"
    FAXES = "faxes"
    PHONECALLS = "phonecalls"
    APPOINTMENTS = "appointments"


class Ignore(Entity):
    PARTNERAPPLICATIONS = "partnerapplications"
    SYSTEMUSERS = "systemusers"
    BUSINESSUNITS = "businessunits"
    ORGANIZATIONS = "organizations"
    TRANSACTIONCURRENCIES = "transactioncurrencies"
    ACCOUNTKPI = "msdyn_accountkpiitems"
    TEAMS = 'teams'


def get_enum_values(cls):
    enum_values = []
    for system in cls:
        enum_values.append(system.value)
    return enum_values


def to_plural(entity: str) -> str:
    return pluralize(entity.lower())


def to_field_name(entity: str) -> str:
    if entity in [member.name for member in Activity]:
        return "activityid"

    return singularize(entity) + "id"


def response_is_error(response: Response):
    try:
        return response.json()["error"]
    except KeyError:
        return None


def notnull(value: object, message: str) -> None:
    """
    Checks if the value is not null and throws an error if it is
    :param value: Value to check
    :param message: Error message to throw
    :return: None
    """
    if not value:
        raise Error(message)
