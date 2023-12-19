from enum import Enum
from gradio import Error
from requests import Response


class Entity(Enum):
    pass


class System(Enum):
    PROD = "myxrm"
    DEV01 = "myxrm-dev01"
    DEV02 = "myxrm-dev02"
    DEV03 = "myxrm-dev03"
    DEV = "myxrm-dev"
    TEST = "myxrm-test"


class Activity(Entity):
    EMAILS = "emails"
    TASKS = "tasks"
    FAXES = "faxes"
    PHONECALLS = "phonecalls"
    APPOINTMENTS = "appointments"


class Ignore(Entity):
    ORGANISATIONS = "organizations"
    BUSINESSUNITS = "businessunits"
    TRANSACTIONCURRENCIES = "transactioncurrencies"
    SYSTEMUSERS = "systemusers"
    SYSTEMUSER = "systemuser"


def get_enum_values(cls):
    enum_values = []
    for system in cls:
        enum_values.append(system.value)
    return enum_values


def to_plural(entity: str) -> str:
    if entity.endswith("s"):
        return entity

    if entity.endswith("y"):
        return entity.lower() + "ies"
    else:
        return entity.lower() + "s"


def to_field_name(entity: str) -> str:
    entity_type = type(entity)

    if entity in [member.name for member in Activity]:
        return "activityid"

    entity = entity[:-1]
    if entity.endswith("ie"):
        return entity[:-2] + "yid"
    else:
        return entity + "id"


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
