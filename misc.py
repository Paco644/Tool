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


class Extension(Enum):
    qualifyingopportunityid = "opportunities"
    afd_channelid = "afd_channels"
    transactioncurrencyid = "transactioncurrencies"
    owninguser = "systemusers"
    ownerid = "systemusers"
    afd_subchannelid = "afd_subchannels"
    owningbusinessunit = "businessunits"
    modifiedby = "systemusers"
    createdby = "systemusers"
    msdyn_accountkpiid = "msdyn_accountkpiitems"
    basecurrencyid = "transactioncurrencies"
    afd_countryid = "afd_countries"
    owningteam = "teams"
    targetgroupid = "afd_targetgroups"
    globalentityiy = "afd_globalentities"
    msdyn_salesaccelerationinsightid = "msdyn_salesaccelerationinsights"
    preferredequipmentid = "equipments"
    slainvokedid = "slas"
    msdyn_leadid = "leads"
    afd_channel = "afd_channels"
    primarycontactid = "contacts"
    managingpartnerid = "accounts"
    createdonbehalfby = "systemusers"
    modifiedonbehalfby = "systemusers"
    msdyn_segmentid = "msdynmkt_segments"
    preferredserviceid = "services"
    organizationid = "organizations"
    modifiedbyexternalparty = "externalparties"
    createdbyexternalparty = "externalparties"
    afd_targetgroupspecificationid = "afd_targetgroupspecifications"
    masterid = "accounts"
    defaultemailserverprofileid = "msdyn_providers"
    defaultpricelevelid = "pricelevels"
    managerid = "systemusers"
    territoryid = "territories"
    originatingleadid = "leads"
    afd_scoringresponsibleuser = "systemusers"
    parentaccountid = "accounts"
    slaid = "slas"
    preferredsystemuserid = "systemusers"
    calendarid = "calendars"
    afd_marketid = "afd_markets"
    parentcustomerid = "systemusers"
    businessunitid = "businessunits"
    afd_saleshub = "afd_saleshubs"
    afd_salesregionid = "afd_salesreagions"
    defaultmailbox = "mailboxes"
    parentsystemuserid = "afd_systems"
    afd_currencyid = "transactioncurrencies"
    queueid = "queues"
    parentbusinessunitid = "businessunits"
    msdyn_accountid = "accounts"
    afd_languageid = "afd_languages"
    msdyn_leadkpiid = "msdyn_leadkpiitems"
    siteid = "sites"
    afd_teamincharge = "teams"
    afd_globalentity = "afd_globalentities"
    msdyn_contactkpiid = "msdyn_contactkpiitems"
    afd_correspondencelanguageid = "afd_languages"
    afd_contact = "contacts"
    campaignid = "campaigns"
    msdyn_contactid = "contacts"
    afd_account = "accounts"
    afd_targetgroupid = "afd_targetgroups"
    parentcontactid = "contacts"
    msdyn_predictivescoreid = "msdyn_predictivescores"
    afd_supportingteammember = "systemusers"
    msa_managingpartnerid = "accounts"
    msdyn_defaultpresenceiduser = "msdyn_presences"
    afd_globalentityid = "afd_globalentities"
    parentterritoryid = "territories"


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
