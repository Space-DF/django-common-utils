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
            settings, "TRANSFORMER_SERVICE_URL", "http://transformer:8080"
        )
        self.timeout = 30

    def _get_device_models_map(self):
        cached = cache.get("transformer:device_models")
        if cached is not None:
            return cached

        endpoint = f"{self.base_url}/api/device-models/"
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
            results = response.json().get("results", [])
            models_map = {str(m["id"]): m for m in results}
            cache.set("transformer:device_models", models_map, timeout=300)
            return models_map
        except RequestException as e:
            logger.error(f"Error fetching device models: {str(e)}")
            return {}

    def get_device_model(self, device_model_id: str):
        models_map = self._get_device_models_map()
        model = models_map.get(str(device_model_id))
        if model is None:
            logger.warning(f"Device model not found: {device_model_id}")
        return model
