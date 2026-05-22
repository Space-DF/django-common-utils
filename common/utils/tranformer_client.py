import logging

import requests
from django.conf import settings
from django.core.cache import cache
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


class TranformerServiceClient:
    """Client for interacting with the Transformer Service API"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or getattr(
            settings, "TRANSFORMER_SERVICE_URL", "http://transformer:8080"  # noqa
        )
        self.timeout = 30

    def get_device_model(self, device_model_id: str):
        """Fetch a specific device model by ID from the Transformer Service API"""
        # Try to get from cache first
        cache_key = f"transformer:device_model:{device_model_id}"  # noqa
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Fetch from direct endpoint
        endpoint = f"{self.base_url}/api/device-models/{device_model_id}"
        try:
            response = requests.get(
                endpoint,
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            model = response.json()
            cache.set(cache_key, model, timeout=300)
            return model
        except RequestException as e:
            logger.error(f"Error fetching device model {device_model_id}: {str(e)}")
            return None
