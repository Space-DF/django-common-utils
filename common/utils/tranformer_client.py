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

    def get_device_profiles_by_model_ids(self, device_model_ids):
        """Fetch multiple device models by ID from the Transformer Service API"""
        ids = sorted(
            {
                str(device_model_id)
                for device_model_id in device_model_ids
                if device_model_id
            }
        )
        if not ids:
            return {}

        cached_profiles = {}
        missing_ids = []
        for device_model_id in ids:
            cache_key = f"transformer:device_model:{device_model_id}"  # noqa
            cached = cache.get(cache_key)
            if cached is not None:
                cached_profiles[device_model_id] = cached
            else:
                missing_ids.append(device_model_id)

        if not missing_ids:
            return cached_profiles

        endpoint = f"{self.base_url}/api/device-models/batch"
        try:
            response = requests.post(
                endpoint,
                json={"device_model_ids": missing_ids},
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            payload = response.json()
        except RequestException as e:
            logger.error(f"Error fetching device models batch: {str(e)}")
            return cached_profiles

        profiles = payload.get("results", payload if isinstance(payload, list) else [])
        for profile in profiles:
            device_model_id = str(profile.get("id") or "").strip()
            if device_model_id:
                cached_profiles[device_model_id] = profile
                cache.set(
                    f"transformer:device_model:{device_model_id}", profile, timeout=300
                )

        return cached_profiles
