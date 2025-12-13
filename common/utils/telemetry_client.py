import logging
from dataclasses import dataclass
from datetime import datetime

import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


def _parse_timestamp(timestamp: str) -> datetime:
    """
    Parse timestamp from various formats
    """
    if isinstance(timestamp, datetime):
        return timestamp

    if isinstance(timestamp, str):
        # Try ISO format first
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt)
            return dt
        except ValueError:
            pass

        # Try other common formats
        formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"]
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp, fmt)
                return timezone.make_aware(dt)
            except ValueError:
                continue

    raise ValueError(f"Unable to parse timestamp: {timestamp}")


@dataclass
class LocationPoint:
    """Data class for a single location point"""

    timestamp: datetime
    latitude: float
    longitude: float
    device_id: str


class TelemetryServiceClient:
    """Client for interacting with the Telemetry Service API"""

    def __init__(self, base_url: str | None = None):
        """
        Initialize the telemetry service client
        """
        self.base_url = base_url or getattr(
            settings, "TELEMETRY_SERVICE_URL", "http://telemetry:8080"
        )
        self.timeout = 30

    def get_location_history(
        self,
        device_id: str,
        organization_slug: str,
        space_slug: str,
        start: datetime,
        end: datetime | None = None,
        limit: int = 10000,
    ) -> list[LocationPoint]:
        """
        Fetch location history for a device from the telemetry service

        Args:
            device_id: The device ID to fetch data for
            space_slug: The space slug
            start: Start timestamp (optional)
            end: End timestamp (optional)
            limit: Maximum number of records to fetch

        Returns:
            List of location data points sorted by timestamp

        Raises:
            RequestException: If the API call fails
        """
        endpoint = f"{self.base_url}/telemetry/v1/location/history"
        params = {"device_id": device_id, "space_slug": space_slug, "limit": limit}

        if start:
            params["start"] = (
                start.isoformat() if isinstance(start, datetime) else start
            )

        if end:
            params["end"] = end.isoformat() if isinstance(end, datetime) else end

        try:
            logger.info("Device ID: %s", device_id)
            logger.info(f"Start: {start}")
            logger.info(f"End: {end}")
            logger.info(f"Limit: {limit}")
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Request params: {params}")

            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Organization": organization_slug,
                },
            )

            logger.info(
                f"Response status code: {response.status_code}, {organization_slug}"
            )

            if response.status_code == 404:
                logger.warning(f"404 - No location data found for device {device_id}")
                return []

            response.raise_for_status()

            data = response.json()
            locations = data.get("locations", [])
            logger.info(f"Received {len(locations)} locations")

            formatted_locations: list[LocationPoint] = []
            for loc in locations:
                formatted_locations.append(
                    LocationPoint(
                        timestamp=_parse_timestamp(loc.get("timestamp", "")),
                        latitude=loc.get("latitude", 0),
                        longitude=loc.get("longitude", 0),
                        device_id=device_id,
                    )
                )

            return formatted_locations
        except Timeout:
            logger.error(
                f"Timeout while fetching location history for device {device_id}"
            )
            raise

        except RequestException as e:
            logger.error(
                f"Error fetching location history for device {device_id}: {str(e)}"
            )
            raise

    def get_widget_data(
        self,
        entity_id: str,
        display_type: str,
        organization_slug: str,
        start_time: str | None = None,
        end_time: str | None = None,
        group_by: str | None = None,
    ) -> dict:
        """
        Fetch widget data for a specific entity from the telemetry service
        """
        endpoint = f"{self.base_url}/telemetry/v1/widget/data/{entity_id}"
        params = {"display_type": display_type}

        if start_time:
            params["start_time"] = start_time

        if end_time:
            params["end_time"] = end_time

        if group_by:
            params["group_by"] = group_by

        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Organization": organization_slug,
                },
            )

            logger.info(f"Widget data response status: {response.status_code}")

            if response.status_code == 404:
                logger.warning(f"404 - No widget data found for entity {entity_id}")
                return {}

            response.raise_for_status()
            return response.json()

        except Timeout:
            logger.error(f"Timeout while fetching widget data for entity {entity_id}")
            raise

        except RequestException as e:
            logger.error(f"Error fetching widget data for entity {entity_id}: {str(e)}")
            raise

    def get_device_properties(
        self,
        device_id: str,
        organization_slug: str,
        space_slug: str,
    ) -> dict:
        """
        Fetch all device properties (all entities data) from telemetry service

        """
        endpoint = f"{self.base_url}/telemetry/v1/data/latest"

        params = {
            "device_id": device_id,
            "space_slug": space_slug,
        }

        try:
            response = requests.get(
                endpoint,
                params=params,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "X-Organization": organization_slug,
                },
            )

            logger.info(f"Device properties response status: {response.status_code}")

            if response.status_code == 404:
                logger.warning(
                    f"404 - No device properties found for device {device_id}"
                )
                return {}

            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(
                f"Error fetching device properties for device {device_id}: {str(e)}"
            )
            raise

    def check_health(self) -> bool:
        """
        Check if the telemetry service is healthy and reachable
        """
        try:
            endpoint = f"{self.base_url}/health"
            response = requests.get(endpoint, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telemetry service health check failed: {str(e)}")
            return False
