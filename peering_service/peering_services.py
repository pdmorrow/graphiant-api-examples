import json
from typing import Any, Optional, Dict
import os
import graphiant_sdk

import errors

ServiceId = int

PUBLISHER_USERNAME_VARIABLE = "GRAPHIANT_PUBLISHER_USERNAME"
PUBLISHER_PASSWORD_VARIABLE = "GRAPHIANT_PUBLISHER_PASSWORD"

PROXY_USERNAME_VARIABLE = "GRAPHIANT_PROXY_USERNAME"
PROXY_PASSWORD_VARIABLE = "GRAPHIANT_PROXY_PASSWORD"
HOST_VARIABLE = "_GRAPHIANT_HOST"  # Internal use only.


class PeeringServicesMgr:
    bearer_token_publisher = ""
    bearer_token_proxy = ""
    host = ""

    def _get_bearer_tokens(self):
        if PUBLISHER_USERNAME_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PUBLISHER_USERNAME_VARIABLE} is not set, please set it to your username"
            )

        if PUBLISHER_PASSWORD_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PUBLISHER_PASSWORD_VARIABLE} is not set, please set it to your password"
            )

        if PROXY_USERNAME_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PROXY_USERNAME_VARIABLE} is not set, please set it to your username"
            )

        if PROXY_PASSWORD_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PROXY_PASSWORD_VARIABLE} is not set, please set it to your password"
            )

        self.host = os.environ.get(HOST_VARIABLE, "https://api.graphiant.com")

        config = graphiant_sdk.Configuration(
            host=self.host,
            username=os.environ[PUBLISHER_USERNAME_VARIABLE],
            password=os.environ[PUBLISHER_PASSWORD_VARIABLE],
        )

        # Initialize API client
        api_client = graphiant_sdk.ApiClient(config)
        self.publisher_api = graphiant_sdk.DefaultApi(api_client)

        # Authenticate and get bearer token
        auth_request = graphiant_sdk.V1AuthLoginPostRequest(
            username=config.username, password=config.password
        )

        try:
            auth_response = self.publisher_api.v1_auth_login_post(
                v1_auth_login_post_request=auth_request
            )
            self.bearer_token_publisher = f"Bearer {auth_response.token}"
        except graphiant_sdk.ApiException as e:
            display_error = (
                json.loads(e.body).get("body", {}).get("displayError", "unknown")
            )
            print(f"Authentication failed for publisher {e.status}: {display_error}")
            exit(1)

        # Now do the same for the proxy.
        config = graphiant_sdk.Configuration(
            host=self.host,
            username=os.environ[PROXY_USERNAME_VARIABLE],
            password=os.environ[PROXY_PASSWORD_VARIABLE],
        )

        # Initialize API client
        api_client = graphiant_sdk.ApiClient(config)
        self.proxy_api = graphiant_sdk.DefaultApi(api_client)

        # Authenticate and get bearer token
        auth_request = graphiant_sdk.V1AuthLoginPostRequest(
            username=config.username, password=config.password
        )

        try:
            auth_response = self.publisher_api.v1_auth_login_post(
                v1_auth_login_post_request=auth_request
            )
            self.bearer_token_proxy = f"Bearer {auth_response.token}"
        except graphiant_sdk.ApiException as e:
            display_error = (
                json.loads(e.body).get("body", {}).get("displayError", "unknown")
            )
            print(f"Authentication failed for proxy {e.status}: {display_error}")
            exit(1)

    def __init__(self):
        self._get_bearer_tokens()

    def __enter__(self):
        self._get_bearer_tokens()

    def __exit__(self):
        pass

    def get_services_summary(self) -> Dict[str, Any]:
        return self.publisher_api.v1_extranets_b2b_general_services_summary_get(
            authorization=self.bearer_token_publisher
        ).to_dict()

    def get_customer_summary(self) -> Dict[str, Any]:
        return self.publisher_api.v1_extranets_b2b_general_customers_summary_get(
            authorization=self.bearer_token_publisher
        ).to_dict()

    def get_customer_match_details(self, customer_id: int) -> Dict[str, Any]:
        url = f"{self.host}/v1/extranets-b2b-peering/match/services/summary?id={customer_id}"
        header_params: Dict[str, Any] = {"Authorization": self.bearer_token_publisher}

        response_data = self.publisher_api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def get_producer_details(self, id: ServiceId) -> Dict[str, Any]:
        url = f"{self.host}/v1/extranets-b2b/{id}/producer?id={id}&type=peering_service"
        header_params: Dict[str, Any] = {"Authorization": self.bearer_token_publisher}

        response_data = self.publisher_api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def get_customer_details(
        self, customer_id: int, service_id: ServiceId
    ) -> Dict[str, Any]:
        url = f"{self.host}/v1/extranets-b2b-peering/consumer/{customer_id}/consumer-details?customerId={customer_id}&serviceId={service_id}"
        header_params: Dict[str, Any] = {"Authorization": self.bearer_token_proxy}

        response_data = self.proxy_api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)
