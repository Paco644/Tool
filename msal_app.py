import os
from configparser import ConfigParser

import msal
import requests
from requests import Response

from record import Record, known_records

from misc import to_field_name, Ignore


class MsalApp:
    """
    Wrapper for the msal library with request features for XRM.
    Implements the singleton pattern to ensure only one instance exists.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self):
        """
        Initializes the application with the API credentials.

        Reads the API credentials from the environment variables and uses them to create
        a `ConfidentialClientApplication` instance for authentication.

        The environment variables should contain the following keys:
        - "tenant_id": The ID of the Azure AD tenant.
        - "client_id": The client ID of the application.
        - "client_secret": The client secret of the application.
        :raises KeyError: If one of the variables does not exist
        """
        try:

            print("Creating confidential client application...")

            config = ConfigParser()
            config.read("conf.ini")
            config = dict(config.items("Authorization"))

            tenant = config["tenantid"]
            client_id = config["clientid"]
            client_secret = config["clientsecret"]
        except KeyError:
            self.app = None
            raise

        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant}",
            client_credential=client_secret,
        )

    def generate_token(self, system) -> str:
        """
        Generates a bearer token for authorization.

        :param system: The system to get access to.
        :type system: str
        :return: The authorization token.
        :rtype: str
        :raises msal.TokenCacheNotFoundError: If the token cache is not found.
        :raises msal.ClientAuthenticationError: If there is an error during client authentication.
        """
        scopes = [f"https://{system}.crm4.dynamics.com/.default"]

        result = self.app.acquire_token_silent(scopes=scopes, account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=scopes)
        return result["access_token"]

    def get(self, system, entity: str, filter: str = None, cache_record: bool = True) -> list[Record]:
        """
        Retrieves data from a specified entity in a system.

        :param cache_record: Flag if the record should be saved in cache for further usage
        :param system: The system to retrieve data from.
        :type system: str
        :param entity: The entity to retrieve data from.
        :type entity: str
        :param filter: The filter to apply to the data retrieval.
        :type filter: str
        :return: A list of objects representing the retrieved data.
        :rtype: list[object]
        """

        url = f"https://{system}.crm4.dynamics.com/api/data/v9.2/{entity}{f"?${filter}" if filter else ""}"
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {self.generate_token(system)}",
                "Prefer"       : 'odata.include-annotations="Microsoft.Dynamics.CRM.lookuplogicalname"',
            },
        )
        records: list[Record] = []

        try:
            response = response.json()["value"]
        except KeyError:
            print(url)

        for item in list(response):
            id = item[to_field_name(entity)]

            if id in known_records:
                record = known_records[id]
                print(f"Getting {record.entity} with id {record.id} from dictionary")
                records.append(record)
            else:
                records.append(Record(system, entity, item, cache_record))

        return records

    def post(self, system, entity: str, payload: object) -> Response:
        """
        Performs a POST request to create a new entity in the specified system.

        :param system: The system to create the entity in.
        :type system: str
        :param entity: The entity to create.
        :type entity: str
        :param payload: The data to be included in the entity.
        :type payload: object
        :return: The response object from the POST request.
        :rtype: object
        """
        url = f"https://{system}.api.crm4.dynamics.com/api/data/v9.2/{entity}"
        return requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.generate_token(system)}",
                "Content-Type": 'application/json',
                "Prefer"       : "return=representation",
            },
            json=payload,
        )

    def patch(self, system, entity: str, id: str, data: object) -> Response:
        """
        Performs a PATCH request to update an entity in the specified system.

        :param system: The system where the entity exists.
        :type system: str
        :param entity: The entity to update.
        :type entity: str
        :param id: The ID of the entity to update.
        :param data: The data to be updated in the entity.
        :type data: object
        :return: The response object from the PATCH request.
        :rtype: object
        """
        url = f"https://{system}.api.crm4.dynamics.com/api/data/v9.2/{entity}({id})"
        return requests.patch(
            url,
            headers={
                "Authorization": f"Bearer {self.generate_token(system)}",
                "Content-Type": 'application/json',
            },
            json=data,
        )


def crm() -> MsalApp:
    return MsalApp()
