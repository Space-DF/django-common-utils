import logging

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class ConsoleServiceClient:
    """Client for interacting with the Console Service API."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or "http://console:80/api"
        self.timeout = 10

    def get_custom_emails(
        self,
        organization_slug: str,
        email_type: str,
    ) -> list[dict]:
        logger.error(f"Fetching from url api {self.base_url}")
        if not self.base_url or not organization_slug:
            return []

        endpoint = f"{self.base_url}/custom-emails"

        try:
            response = requests.get(
                endpoint,
                params={"email_type": email_type},
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Organization": organization_slug,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload.get("results") or []
        except RequestException as exc:
            logger.error(
                "Error fetching custom emails for organization %s from console service: %s",
                organization_slug,
                exc,
            )
            return []
