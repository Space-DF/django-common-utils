import logging

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class ConsoleServiceClient:
    """Client for interacting with the Console Service API."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or "http://console:80/api"
        self.timeout = 10

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def get_custom_emails(
        self,
        organization_slug: str,
        email_type: str,
    ) -> list[dict]:
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

    def reserve_quota(
        self,
        organization_slug: str,
        feature: str | list[str],
        amount: int = 1,
    ) -> tuple[bool, str | None]:
        """Reserve quota for one or more features.

        Returns ``(reserved, error)``. On network error or missing billing
        data the reservation is treated as successful (fail-open) so that
        billing infra problems never block the core product.
        """
        endpoint = f"{self.base_url}/billing/internal/quota/reserve"
        try:
            response = requests.post(
                endpoint,
                json={
                    "organization": organization_slug,
                    "feature": feature,
                    "amount": amount,
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
        except RequestException as exc:
            logger.warning(
                "reserve_quota HTTP failed for %s/%s: %s — failing open",
                organization_slug,
                feature,
                exc,
            )
            return True, None

        if response.status_code == 200:
            return True, None
        if response.status_code == 403:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = "Quota exceeded."
            return False, detail
        # Unexpected status — fail open with a warning.
        logger.warning(
            "reserve_quota unexpected status %s for %s/%s — failing open",
            response.status_code,
            organization_slug,
            feature,
        )
        return True, None

    def release_quota(
        self,
        organization_slug: str,
        feature: str | list[str],
        amount: int = 1,
    ) -> None:
        """Release previously reserved quota for one or more features."""
        endpoint = f"{self.base_url}/billing/internal/quota/release"
        try:
            requests.post(
                endpoint,
                json={
                    "organization": organization_slug,
                    "feature": feature,
                    "amount": amount,
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
        except RequestException as exc:
            logger.warning(
                "release_quota HTTP failed for %s/%s: %s",
                organization_slug,
                feature,
                exc,
            )

    def get_quota(
        self,
        organization_slug: str,
        feature: str | list[str],
    ) -> tuple[dict | None, str | None]:
        """View current quota usage for one or more features.

        Returns ``(data, error)`` matching the reserve/release pattern.
        """
        endpoint = f"{self.base_url}/billing/quota"
        try:
            response = requests.post(
                endpoint,
                json={
                    "organization": organization_slug,
                    "feature": feature,
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json(), None
        except RequestException as exc:
            logger.warning(
                "get_quota HTTP failed for %s/%s: %s",
                organization_slug,
                feature,
                exc,
            )
            return None, str(exc)


console_client = ConsoleServiceClient()
