import json
import os
import logging
from typing import List, Any

import msal
import requests

from requests import Response

static_data = json.load(open("static_data.json"))
logging.basicConfig(
    format="%(asctime)s - %(levelname)s -> \t %(message)s",
    filemode="w",
    datefmt="%d/%m/%Y %I:%M:%S",
    filename=f"latest.log",
    encoding="utf-8",
    level=logging.NOTSET,
)


class App:
    """
    Wrapper for the msal library with request features for XRM
    """

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

        logging.info("Initializing MSAL")

        try:
            tenant = os.environ["tenant_id"]
            client_id = os.environ["client_id"]
            client_secret = os.environ["client_secret"]
        except KeyError:
            self.app = None
            logging.error(
                "Error while initializing MSAL application. Missing environment variables for "
                "authentication!"
            )
            return

        self.app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant}",
            client_credential=client_secret,
        )

        logging.info(
            "Successfully established a connection and created the client application"
        )

    def generate_token(self, system: str) -> str:
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

    def get(self, system: str, entity: str, filter="") -> list[Any]:
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
        logging.info(f"GET {url}")
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.generate_token(system)}"},
        )

        return list(response.json()["value"])

    def post(self, system: str, entity: str, payload) -> Response:
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
        logging.info(f"POST {url}")

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
        logging.info(f"PATCH {url}")
        return requests.patch(
            url,
            data,
            headers={"Authorization": f"Bearer {self.generate_token(system)}"},
            json=json.dumps(data),
        )


# misc functions
def to_field_name(entity: str) -> str:
    """
    Converts an entity name to its corresponding field name.

    :param entity: The name of the entity.
    :type entity: str
    :return: The corresponding field name.
    :rtype: str
    """
    if entity in static_data["activities"]:
        return "activityid"

    entity = entity[:-1]
    if entity.endswith("ie"):
        return entity[:-2] + "yid"
    else:
        return entity + "id"


def to_plural(entity: str) -> str:
    """
    Converts an entity name to its plural form.

    :param entity: The name of the entity.
    :type entity: str
    :return: The plural form of the entity name.
    :rtype: str
    """
    if entity.endswith("y"):
        return entity.lower() + "ies"
    else:
        return entity.lower() + "s"
