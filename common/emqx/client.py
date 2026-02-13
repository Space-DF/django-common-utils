"""
Utility for managing EMQX connectors, actions, and rules via the REST API.

Each RabbitMQ vhost gets its own MQTT connector, action, and rule so that tenant
traffic is isolated. Connector usernames follow the "vhost:user" convention
expected by the RabbitMQ MQTT plugin.
"""

import logging
from typing import Iterable, Sequence
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EMQXClient:
    def __init__(self, token: str | None = None) -> None:
        self.session = requests.Session()
        self.base_url = settings.EMQX_API_URL.rstrip("/")
        self.rule_prefix = getattr(settings, "EMQX_RULE_ID", "rabbitmq_device_messages")
        self.default_rule_sql = getattr(
            settings,
            "EMQX_RULE_SQL",
            'SELECT * FROM "tenant/+/device/data"',
        )

        self.token = token
        if not self.token:
            username = getattr(settings, "EMQX_USERNAME")
            password = getattr(settings, "EMQX_PASSWORD")
            if username and password:
                self.token = self.get_token(username, password)
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.debug("EMQXClient initialized with Bearer token authentication")
        else:
            logger.warning("EMQXClient initialized without authentication token")

    def get_token(self, username: str, password: str) -> str:
        try:
            resp = self.session.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
            )
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("token")
            if not token:
                raise ValueError("No token returned from EMQX login endpoint")

            return token
        except requests.HTTPError as e:
            logger.error(f"Failed to authenticate with EMQX: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting EMQX token for user: {e}")
            raise

    def _log_and_raise(self, resp: requests.Response) -> None:
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            payload = resp.text
        logger.error(
            "EMQX API call failed (%s %s): %s",
            resp.request.method,
            resp.request.url,
            payload,
        )
        resp.raise_for_status()

    @staticmethod
    def _sanitize(name: str) -> str:
        return "".join(char if char.isalnum() or char == "_" else "_" for char in name)

    def _action_name(self, vhost: str) -> str:
        return f"device_messages_{self._sanitize(vhost)}"

    def _rule_id_for_vhost(self, vhost: str) -> str:
        return f"{self.rule_prefix}_{self._sanitize(vhost)}"

    def _build_rule_sql(self, slugs: Sequence[str]) -> str:
        unique_slugs = sorted({slug for slug in slugs if slug})
        if not unique_slugs:
            raise ValueError("At least one slug required to build vhost rule SQL")

        base_sql = self.default_rule_sql.strip()
        slug_list = ", ".join(f"'{slug}'" for slug in unique_slugs)
        slug_clause = f"topic(2) IN ({slug_list})"

        if " where " in base_sql.lower():
            return f"{base_sql} AND ({slug_clause})"

        return f"{base_sql} WHERE {slug_clause}"

    @staticmethod
    def _is_duplicate_action(resp: requests.Response) -> bool:
        if resp.status_code not in (400, 409):
            return False
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            return False
        code = payload.get("code")
        message = payload.get("message", "")
        return code == "ALREADY_EXISTS" or (
            isinstance(message, str) and "already exists" in message.lower()
        )

    def _connector_id(self, connector_name: str) -> str:
        return f"mqtt:{connector_name}"  # noqa: E231

    def _action_id(self, action_name: str) -> str:
        return f"mqtt:{action_name}"  # noqa: E231

    def connector_name(self, vhost: str) -> str:
        return f"mqtt_{self._sanitize(vhost)}"  # noqa: E231

    @staticmethod
    def _is_duplicate_connector(resp: requests.Response) -> bool:
        if resp.status_code not in (400, 409):
            return False
        try:
            payload = resp.json()
        except Exception:  # noqa: BLE001
            return False
        code = payload.get("code")
        message = payload.get("message", "")
        return code == "ALREADY_EXISTS" or (
            isinstance(message, str) and "already exists" in message.lower()
        )

    def ensure_connector(
        self,
        vhost: str,
        rabbit_user: str,
        rabbit_pass: str,
        pool_size: int = 1,
    ) -> str:
        connector_name = self.connector_name(vhost)
        payload = {
            "type": "mqtt",
            "name": connector_name,
            "enable": True,
            "server": f"{settings.RABBITMQ_HOST}:{settings.RABBITMQ_MQTT_PORT}",  # noqa: E231
            "username": f"{vhost}:{rabbit_user}",  # noqa: E231
            "password": rabbit_pass,
            "pool_size": pool_size,
        }

        resp = self.session.post(f"{self.base_url}/connectors", json=payload)
        if resp.status_code in (200, 201):
            logger.info("Created EMQX connector %s for vhost %s", connector_name, vhost)
            return connector_name
        if resp.status_code == 409 or self._is_duplicate_connector(resp):
            update = self.session.put(
                f"{self.base_url}/connectors/mqtt:{connector_name}",  # noqa: E231
                json={
                    "server": payload["server"],
                    "username": payload["username"],
                    "password": payload["password"],
                    "pool_size": pool_size,
                },
            )
            if update.status_code >= 400:
                self._log_and_raise(update)
            return connector_name

        self._log_and_raise(resp)
        return connector_name

    def ensure_vhost_action(
        self,
        vhost: str,
        connector_name: str,
        topic: str = "${topic}",
    ) -> str:
        action_name = self._action_name(vhost)
        payload = {
            "type": "mqtt",
            "name": action_name,
            "enable": True,
            "connector": connector_name,
            "parameters": {"topic": topic, "qos": 1, "retain": False},
        }

        resp = self.session.post(f"{self.base_url}/actions", json=payload)
        if resp.status_code in (200, 201):
            logger.info(
                "Created EMQX action %s for connector %s", action_name, connector_name
            )
            return action_name
        if resp.status_code == 409 or self._is_duplicate_action(resp):
            update = self.session.put(
                f"{self.base_url}/actions/mqtt:{action_name}",  # noqa: E231
                json={
                    "connector": connector_name,
                    "parameters": {"topic": topic, "qos": 1, "retain": False},
                    "enable": True,
                },
            )
            if update.status_code >= 400:
                self._log_and_raise(update)
            return action_name

        self._log_and_raise(resp)
        return action_name

    def ensure_vhost_rule(self, vhost: str, slugs: Iterable[str]) -> None:
        slug_list = list(slugs)
        if not slug_list:
            raise ValueError("At least one slug required for rule creation")

        rule_id = self._rule_id_for_vhost(vhost)
        sql = self._build_rule_sql(slug_list)
        action_id = self._action_id(self._action_name(vhost))
        rule_url = f"{self.base_url}/rules/{rule_id}"
        payload = {
            "sql": sql,
            "actions": [action_id],
            "enable": True,
        }

        resp = self.session.get(rule_url)
        if resp.status_code == 200:
            update = self.session.put(rule_url, json=payload)
            if update.status_code >= 400:
                self._log_and_raise(update)
            logger.info("Updated EMQX rule %s for vhost %s", rule_id, vhost)
            return
        if resp.status_code == 404:
            create_payload = {
                "id": rule_id,
                "name": rule_id,
                "description": f"Forward tenant MQTT traffic for vhost {vhost}",
                "sql": sql,
                "actions": [action_id],
                "enable": True,
            }
            create = self.session.post(f"{self.base_url}/rules", json=create_payload)
            if create.status_code >= 400:
                self._log_and_raise(create)
            logger.info("Created EMQX rule %s for vhost %s", rule_id, vhost)
            return

        self._log_and_raise(resp)

    def delete_vhost_rule(self, vhost: str) -> None:
        rule_id = self._rule_id_for_vhost(vhost)
        resp = self.session.delete(f"{self.base_url}/rules/{rule_id}")
        if resp.status_code in (200, 204, 404):
            logger.info("Deleted EMQX rule %s for vhost %s", rule_id, vhost)
            return
        self._log_and_raise(resp)

    def delete_connector(self, vhost: str) -> None:
        connector_id = self._connector_id(self.connector_name(vhost))
        resp = self.session.delete(f"{self.base_url}/connectors/{connector_id}")
        if resp.status_code in (200, 204, 404):
            return
        self._log_and_raise(resp)

    def delete_action(self, vhost: str) -> None:
        action_id = self._action_id(self._action_name(vhost))
        resp = self.session.delete(f"{self.base_url}/actions/{action_id}")
        if resp.status_code in (200, 204, 404):
            return
        self._log_and_raise(resp)

    def teardown_tenant(self, vhost: str, remaining_slugs: Iterable[str]) -> None:
        slugs = sorted({slug for slug in remaining_slugs if slug})
        if slugs:
            self.ensure_vhost_rule(vhost, slugs)
            return

        self.delete_vhost_rule(vhost)
        self.delete_action(vhost)
        self.delete_connector(vhost)

    def disconnect_client(self, client_id: str) -> None:
        client_path = quote(client_id, safe="")
        resp = self.session.delete(f"{self.base_url}/clients/{client_path}")
        if resp.status_code in (200, 202, 204, 404):
            return
        self._log_and_raise(resp)
