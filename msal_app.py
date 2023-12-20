import json
import os
import msal
import requests
from requests import Response

from record import Record

from misc import System


class App_do_not_use:
    """
    Wrapper for the msal library with request features for XRM
    """

    first_init = True

    def __init__(self):
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

        if not self.first_init:
            return

        try:
            print("Creating confidential client application...")
            tenant = os.environ["tenant_id"]
            client_id = os.environ["client_id"]
            client_secret = os.environ["client_secret"]
        except KeyError:
            self.app = None
            exit(0)

        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant}",
            client_credential=client_secret,
        )

        self.first_init = False

    def generate_token(self, system: System) -> str:
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

    def get(self, system: System, entity: str, filter="") -> list[Record]:
        """
        Retrieves data from a specified entity in a system.

        :param system: The system to retrieve data from.
        :type system: str
        :param entity: The entity to retrieve data from.
        :type entity: str
        :param filter: The filter to apply to the data retrieval.
        :type filter: str
        :return: A list of objects representing the retrieved data.
        :rtype: list[object]
        """
        url = f"https://{system}.crm4.dynamics.com/api/data/v9.2/{entity}?${filter}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.generate_token(system)}"},
        )
        records: list[Record] = []
        for item in list(response.json()["value"]):
            records.append(Record(system, entity, item))
        return records

    def post(self, system: System, entity: str, payload) -> Response:
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
                "Prefer": "return=representation",
            },
            json=json.dumps(payload),
        )

    def patch(self, system, entity, id, data) -> object:
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
            data,
            headers={"Authorization": f"Bearer {self.generate_token(system)}"},
            json=json.dumps(data),
        )


class MsalApp(App_do_not_use):
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(App_do_not_use, cls).__new__(cls)
        return cls.instance


def crm() -> MsalApp:
    return MsalApp()
