import logging
from os import getenv

import requests

logger = logging.getLogger(__name__)


class NYTApiService:
    """
    Service for making calls to the New York Times API. Responsible for collecting query parameters and configuration,
    making requests, and handling responses.
    """
    def get_best_sellers():
        """
        Retrieve a list of NYT Books Best Sellers from the source API. Any response code other than HTTP 200 (OK) is
        considered an error because HTTP 200 is the only listed successful response code on the NYT API documentation
        site.
        """
        params = {"api-key": getenv("NYT_API_KEY")}
        response = requests.get(
            url=getenv("NYT_BEST_SELLERS_ENDPOINT_URL"),
            params=params,
            headers={"Accept": "application/json"},
            allow_redirects=False,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()

        logger.warning(f"[NYTApiService] Received unexpected response code from NYT API: {response.status_code}")

        # Undocumented but successful response codes should be investigated further. Maybe we missed something.
        if response.status_code > 200 and response.status_code < 300:
            raise Exception("Unexpected response code")

        # HTTP 3xx response codes might signal that the API has been moved, or that `NYT_BEST_SELLERS_ENDPOINT_URL` was
        # misconfigured. The endpoint URL should be updated.
        if response.status_code >= 300 and response.status_code < 400:
            raise Exception("Possible misconfiguration")

        # HTTP 4xx response codes might signal that our API key expired or that we sent a malformed request (e.g. if we
        # missed something in validation).
        if response.status_code >= 400 and response.status_code < 500:
            raise Exception("Client error")

        # HTTP 5xx response codes signal an error on the NYT side.
        raise Exception("Target API error")
