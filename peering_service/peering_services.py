"""
Wrapper routines around the Graphiant API, the idea is to hide complexity
away from the caller.
"""

from ipaddress import IPv4Network
import json
from typing import Any, List, Optional, Dict, Tuple
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

    def _get_publisher_bearer_token(self):
        """
        Get a bearer token for the proxy tenant, all requests to this account
        must use the returned bearer token for authorisation.

        N.B. tokens by default are only valid for 15 minutes.
        """
        if self.bearer_token_publisher != "":
            # Already got a token.
            return

        if PUBLISHER_USERNAME_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PUBLISHER_USERNAME_VARIABLE} is not set, please set it to your username"
            )

        if PUBLISHER_PASSWORD_VARIABLE not in os.environ:
            raise errors.PeeringServiceClientError(
                f"Environment variable {PUBLISHER_PASSWORD_VARIABLE} is not set, please set it to your password"
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
            print(
                f"Authentication failed for publisher tenant {e.status}: {display_error}"
            )
            exit(1)

    def _get_proxy_token(self):
        """
        Get a bearer token for the proxy tenant, all requests to this account
        must use the returned bearer token for authorisation.

        N.B. tokens by default are only valid for 15 minutes.
        """
        if self.bearer_token_proxy != "":
            # Already got a token.
            return

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
            auth_response = self.proxy_api.v1_auth_login_post(
                v1_auth_login_post_request=auth_request
            )
            self.bearer_token_proxy = f"Bearer {auth_response.token}"
        except graphiant_sdk.ApiException as e:
            display_error = (
                json.loads(e.body).get("body", {}).get("displayError", "unknown")
            )
            print(
                f"Authentication failed for customer tenant {e.status}: {display_error}"
            )
            exit(1)

    def get_services_summary(self, context: str) -> Dict[str, Any]:
        if context == "publisher":
            self._get_publisher_bearer_token()
            api = self.publisher_api
            token = self.bearer_token_publisher
        else:
            self._get_proxy_token()
            api = self.proxy_api
            token = self.bearer_token_proxy

        return api.v1_extranets_b2b_general_services_summary_get(
            authorization=token
        ).to_dict()

    def get_customer_summary(self) -> Dict[str, Any]:
        self._get_publisher_bearer_token()
        return self.publisher_api.v1_extranets_b2b_general_customers_summary_get(
            authorization=self.bearer_token_publisher
        ).to_dict()

    def get_customer_match_details(self, customer_id: int) -> Dict[str, Any]:
        self._get_publisher_bearer_token()
        url = f"{self.host}/v1/extranets-b2b-peering/match/services/summary?id={customer_id}"
        header_params: Dict[str, Any] = {"Authorization": self.bearer_token_publisher}

        response_data = self.publisher_api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def get_producer_details(self, id: ServiceId) -> Dict[str, Any]:
        self._get_publisher_bearer_token()
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
        self._get_proxy_token()
        url = f"{self.host}/v1/extranets-b2b-peering/consumer/{customer_id}/consumer-details?customerId={customer_id}&serviceId={service_id}"
        header_params: Dict[str, Any] = {"Authorization": self.bearer_token_proxy}

        response_data = self.proxy_api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def _get_lan_segments(self, context: str) -> Dict[str, Any]:
        if context == "publisher":
            self._get_publisher_bearer_token()
            api = self.publisher_api
            token = self.bearer_token_publisher
        else:
            self._get_proxy_token()
            api = self.proxy_api
            token = self.bearer_token_proxy

        url = f"{self.host}/v1/global/lan-segments"
        header_params: Dict[str, Any] = {"Authorization": token}

        response_data = api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def get_lan_segments(self, context: str) -> Dict[str, Any]:
        return self._get_lan_segments(context)

    def get_lan_segment_by_id(self, context: str, id: int) -> Dict[str, Any]:
        d = self._get_lan_segments(context)
        entries = d.get("entries", [])
        for e in entries:
            if id == e.get("id"):
                r = {}
                r["entries"] = [e]
                return r

        return {}

    def get_lan_segment_by_name(self, context: str, name: str) -> Dict[str, List[Any]]:
        d = self._get_lan_segments(context)
        entries = d.get("entries", [])
        for e in entries:
            if name == e.get("name"):
                r = {}
                r["entries"] = [e]
                return r

        return {}

    def _get_sites(self, context: str, id: Optional[int] = None):
        if context == "publisher":
            self._get_publisher_bearer_token()
            api = self.publisher_api
            token = self.bearer_token_publisher
        else:
            self._get_proxy_token()
            api = self.proxy_api
            token = self.bearer_token_proxy

        url = f"{self.host}/v1/sites/details"
        header_params: Dict[str, Any] = {"Authorization": token}

        response_data = api.api_client.call_api(
            method="GET", url=url, header_params=header_params
        )
        response_data.read()
        return json.loads(response_data.data)

    def get_sites(self, context) -> Dict[str, Any]:
        return self._get_sites(context)

    def get_site_by_id(self, context: str, id: int) -> Dict[str, Any]:
        d = self._get_sites(context)
        entries = d.get("sites", [])
        for e in entries:
            if id == e.get("id"):
                r = {}
                r["sites"] = [e]
                return r

        return {}

    def get_site_by_name(self, context: str, name: str) -> Dict[str, Any]:
        d = self._get_sites(context)
        entries = d.get("sites", [])
        for e in entries:
            if name == e.get("name"):
                r = {}
                r["sites"] = [e]
                return r

        return {}

    def get_edges(
        self, context: str, device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return the edges associated with the login session.
        """
        if context == "publisher":
            self._get_publisher_bearer_token()
            api = self.publisher_api
            token = self.bearer_token_publisher
        else:
            self._get_proxy_token()
            api = self.proxy_api
            token = self.bearer_token_proxy

        return api.v1_edges_summary_get(authorization=token).to_dict()

    def create_producer(
        self,
        name: str,
        desc: str,
        prefix_and_tag_set: List[Tuple[IPv4Network, Optional[str]]],
        site_names: List[str],
        service_lan_seg: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a peering service producer (aka publisher).

        name: Name of the service.
        desc: Description of the service.
        prefix_and_tag_set: List of tuples in the form (prefix, tag), tag is optional.
        service_lan_seg: The lan segment (vrf) that the service is attached to.
        """

        payload = graphiant_sdk.V1ExtranetsB2bPeeringProducerPostRequest()
        payload.service_name = name
        payload.type = "peering_service"
        payload.policy = graphiant_sdk.V1ExtranetsB2bPeeringProducerPostRequestPolicy()

        payload.policy.description = desc
        payload.policy.type = "peering_service"
        # Get the lan segment ID.
        lan_seg_entry = self.get_lan_segment_by_name(
            context="publisher", name=service_lan_seg
        )
        if not lan_seg_entry:
            print(f"No such lan segment {service_lan_seg}")
            return None

        lan_seg = lan_seg_entry.get("entries")
        if not lan_seg:
            print(f"No entries found for lan segment {service_lan_seg}")
            return None

        lan_seg_id = lan_seg[0].get("id")

        payload.policy.service_lan_segment = lan_seg_id
        payload.policy.prefix_tags = []
        for pt in prefix_and_tag_set:
            entry = (
                graphiant_sdk.V1ExtranetsB2bPeeringMatchServiceToCustomerPostRequestServiceServicePrefixesInner()
            )
            entry.prefix = str(pt[0])
            entry.tag = pt[1]
            payload.policy.prefix_tags.append(entry)

        sites = graphiant_sdk.V1ExtranetsB2bConsumerPostRequestSiteInformationInner()
        sites.sites = []
        # Get the site it.
        for site_name in site_names:
            s = self.get_site_by_name(context="publisher", name=site_name)
            if s:
                sn = s.get("sites", [])
                if sn:
                    sites.sites.append(sn[0].get("id"))

        if not sites.sites:
            print(f"No valid sites found, input was: {site_names}")
            return None

        payload.policy.site = [sites]

        payload.policy.global_object_ops = {}

        return self.publisher_api.v1_extranets_b2b_peering_producer_post(
            authorization=self.bearer_token_publisher,
            v1_extranets_b2b_peering_producer_post_request=payload,
        ).to_dict()
