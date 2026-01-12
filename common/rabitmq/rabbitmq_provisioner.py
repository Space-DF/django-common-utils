"""
RabbitMQ Provisioner for Multi-Tenant Architecture

Handles vhost, user, queue, exchange, and binding provisioning for organizations.
"""

import logging
import time
from typing import Dict, Optional, Set
from urllib.parse import quote, urlparse, urlunparse

import requests
from django.conf import settings

from common.emqx import EMQXClient

logger = logging.getLogger(__name__)


class RabbitMQProvisionerError(Exception):
    """Base exception for RabbitMQ provisioner errors"""

    pass


class RabbitMQProvisioner:
    """Provisions RabbitMQ resources for multi-tenant architecture"""

    # Configuration for load balancing
    MAX_QUEUES_PER_VHOST = 100  # Create new vhost if existing ones have more queues (Assume 50 tenants in a vhost)
    VHOST_PREFIX = ""  # Prefix for shared vhosts

    def __init__(self):
        self.api_url = settings.RABBITMQ_MANAGEMENT_API_URL.rstrip("/")
        self.admin_user = settings.RABBITMQ_DEFAULT_USER
        self.admin_password = settings.RABBITMQ_DEFAULT_PASSWORD
        self.session = requests.Session()
        self.session.auth = (self.admin_user, self.admin_password)
        self.session.headers.update({"Content-Type": "application/json"})

    def _encode(self, value: str) -> str:
        """Percent-encode RabbitMQ resource identifiers for HTTP endpoints"""
        return quote(value, safe="")

    def build_tenant_amqp_url(self, vhost_name: str) -> str:
        """
        Build a tenant-specific AMQP URL by swapping the vhost portion of the base URL.
        """
        base_url = settings.RABBITMQ_URL
        parsed = urlparse(base_url)

        if vhost_name:
            encoded_vhost = self._encode(vhost_name)
            parsed = parsed._replace(path=f"/{encoded_vhost}")
        else:
            parsed = parsed._replace(path="/")

        return urlunparse(parsed)

    def list_vhosts(self) -> Set[str]:
        """
        Return a set of vhost names currently present in RabbitMQ.
        """
        try:
            response = self.session.get(f"{self.api_url}/api/vhosts")
            response.raise_for_status()
            return {
                entry.get("name")
                for entry in response.json()
                if entry.get("name") is not None
            }
        except requests.RequestException as e:
            logger.error("Failed to list RabbitMQ vhosts: %s", e)
            return set()

    def get_vhost_load(self, vhost_name: str) -> Dict:
        """
        Get load metrics for a vhost
        Returns:
            Dict with queue_count, connection_count, message_count
        """
        try:
            # Get queues in vhost
            encoded_vhost = self._encode(vhost_name)
            response = self.session.get(f"{self.api_url}/api/queues/{encoded_vhost}")
            response.raise_for_status()
            queues = response.json()

            queue_count = len(queues)
            message_count = sum(q.get("messages", 0) for q in queues)

            # Get connections to vhost
            response = self.session.get(f"{self.api_url}/api/vhosts/{encoded_vhost}")
            response.raise_for_status()

            return {
                "vhost": vhost_name,
                "queue_count": queue_count,
                "message_count": message_count,
                "load_score": queue_count * 10 + message_count,  # Simple load metric
            }
        except requests.RequestException as e:
            logger.warning(f"Failed to get load for vhost {vhost_name}: {e}")
            return {
                "vhost": vhost_name,
                "queue_count": 0,
                "message_count": 0,
                "load_score": 0,
            }

    def get_least_loaded_vhost(self) -> Optional[str]:
        """
        Find the least-loaded tenant vhost pool

        Returns:
            Vhost name or None if all vhosts are overloaded or none exist
        """
        try:
            # Get all vhosts
            response = self.session.get(f"{self.api_url}/api/vhosts")
            response.raise_for_status()
            all_vhosts = response.json()

            # All vhost starting with VHOST_PREFIX are tenant pools
            # Exclude default vhost "/"
            tenant_vhosts = [
                v["name"]
                for v in all_vhosts
                if v["name"].startswith(self.VHOST_PREFIX) and v["name"] != "/"
            ]

            logging.info(f"Found tenant pool vhosts: {tenant_vhosts}")

            if not tenant_vhosts:
                logger.info("No tenant pool vhosts found")
                return None

            # Get load for each vhost
            vhost_loads = [self.get_vhost_load(vhost) for vhost in tenant_vhosts]

            # Find least loaded vhost that's not overloaded
            least_loaded = min(vhost_loads, key=lambda x: x["load_score"])

            if least_loaded["queue_count"] >= self.MAX_QUEUES_PER_VHOST:
                logger.info(
                    f"All vhosts are at capacity (max: {self.MAX_QUEUES_PER_VHOST}). "
                    f"Least loaded has {least_loaded['queue_count']} queues"
                )
                return None

            logger.info(
                f"Selected least-loaded vhost: {least_loaded['vhost']} "
                f"(queues: {least_loaded['queue_count']}, "
                f"messages: {least_loaded['message_count']})"
            )
            return least_loaded["vhost"]

        except requests.RequestException as e:
            logger.error(f"Failed to get vhost list: {e}")
            return None

    def create_vhost(self, vhost_name: str) -> bool:
        """Create vhost for organization"""
        try:
            encoded_vhost = self._encode(vhost_name)
            response = self.session.put(
                f"{self.api_url}/api/vhosts/{encoded_vhost}",
                json={"description": f"Vhost for {vhost_name}", "tracing": False},
            )
            response.raise_for_status()
            logger.info(f"Created vhost: {vhost_name}")

            try:
                emqx_client = EMQXClient()
                emqx_client.ensure_connector(
                    vhost=vhost_name,
                    rabbit_user=settings.RABBITMQ_DEFAULT_USER,
                    rabbit_pass=settings.RABBITMQ_DEFAULT_PASSWORD,
                )
                emqx_client.ensure_vhost_action(
                    vhost=vhost_name,
                    connector_name=emqx_client.connector_name(vhost_name),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to configure EMQX connector for new vhost {vhost_name}: {str(e)}"
                )
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create vhost {vhost_name}: {e}")
            raise RabbitMQProvisionerError(f"Failed to create vhost: {e}")

    def create_user(self, username: str, password: str) -> bool:
        """Create dedicated user for organization"""
        try:
            encoded_user = self._encode(username)
            response = self.session.put(
                f"{self.api_url}/api/users/{encoded_user}",
                json={"password": password, "tags": "monitoring"},
            )
            response.raise_for_status()
            logger.info(f"Created user: {username}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create user {username}: {e}")
            raise RabbitMQProvisionerError(f"Failed to create user: {e}")

    def set_permissions(self, vhost_name: str, username: str) -> bool:
        """Set user permissions for vhost"""
        try:
            encoded_vhost = self._encode(vhost_name)
            encoded_user = self._encode(username)
            response = self.session.put(
                f"{self.api_url}/api/permissions/{encoded_vhost}/{encoded_user}",
                json={"configure": ".*", "write": ".*", "read": ".*"},
            )
            response.raise_for_status()
            logger.info(f"Set permissions for {username} on {vhost_name}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to set permissions: {e}")
            raise RabbitMQProvisionerError(f"Failed to set permissions: {e}")

    def create_exchange(self, vhost_name: str, exchange_name: str) -> bool:
        """Create exchange for tenant"""
        try:
            encoded_vhost = self._encode(vhost_name)
            encoded_exchange = self._encode(exchange_name)
            response = self.session.put(
                f"{self.api_url}/api/exchanges/{encoded_vhost}/{encoded_exchange}",
                json={
                    "type": "topic",
                    "durable": True,
                    "auto_delete": False,
                    "internal": False,
                    "arguments": {},
                },
            )
            response.raise_for_status()
            logger.info(f"Created exchange: {exchange_name} in {vhost_name}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create exchange: {e}")
            raise RabbitMQProvisionerError(f"Failed to create exchange: {e}")

    def create_queue(self, vhost_name: str, queue_name: str) -> bool:
        """Create queue for tenant"""
        try:
            encoded_vhost = self._encode(vhost_name)
            encoded_queue = self._encode(queue_name)
            response = self.session.put(
                f"{self.api_url}/api/queues/{encoded_vhost}/{encoded_queue}",
                json={
                    "durable": True,
                    "auto_delete": False,
                    "arguments": {
                        "x-max-length": 100000,
                        "x-message-ttl": 86400000,  # 24 hours
                        "x-overflow": "reject-publish",
                    },
                },
            )
            response.raise_for_status()
            logger.info(f"Created queue: {queue_name} in {vhost_name}")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create queue: {e}")
            raise RabbitMQProvisionerError(f"Failed to create queue: {e}")

    def create_binding(
        self, vhost_name: str, exchange: str, queue: str, routing_key: str
    ) -> bool:
        """Create binding between exchange and queue"""
        try:
            encoded_vhost = self._encode(vhost_name)
            encoded_exchange = self._encode(exchange)
            encoded_queue = self._encode(queue)
            response = self.session.post(
                f"{self.api_url}/api/bindings/{encoded_vhost}/e/{encoded_exchange}/q/{encoded_queue}",
                json={"routing_key": routing_key, "arguments": {}},
            )
            response.raise_for_status()
            logger.info(f"Created binding: {exchange} -> {queue} (key: {routing_key})")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create binding: {e}")
            raise RabbitMQProvisionerError(f"Failed to create binding: {e}")

    def create_exchange_binding(
        self,
        vhost_name: str,
        source_exchange: str,
        destination_exchange: str,
        routing_key: str,
    ) -> bool:
        """Create binding between two exchanges (exchange-to-exchange)"""
        try:
            encoded_vhost = self._encode(vhost_name)
            encoded_source = self._encode(source_exchange)
            encoded_destination = self._encode(destination_exchange)
            response = self.session.post(
                f"{self.api_url}/api/bindings/{encoded_vhost}/e/{encoded_source}/e/{encoded_destination}",
                json={"routing_key": routing_key, "arguments": {}},
            )
            response.raise_for_status()
            logger.info(
                f"Created exchange binding: {source_exchange} -> {destination_exchange} (key: {routing_key})"
            )
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to create exchange binding: {e}")
            raise RabbitMQProvisionerError(f"Failed to create exchange binding: {e}")

    def get_organization_slugs(
        self, vhost_name: str, org_slug: str = None, exclude: bool = False
    ) -> list:
        """
        Get organization slugs for a given vhost.

        Handles two cases:
        1. organization-service (no database/models): Returns only the provided org_slug
        2. console-service and other services (with models): Queries database for all slugs
        """
        try:
            from apps.organization.models import Organization

            query = Organization.objects.filter(rabbitmq_vhost=vhost_name)

            if exclude and org_slug:
                query = query.exclude(slug_name=org_slug)

            slugs = list(query.values_list("slug_name", flat=True))
            if not exclude and org_slug and org_slug not in slugs:
                slugs.append(org_slug)

            logger.info(
                f"[CONSOLE-SERVICE] Retrieved organization slugs from database for vhost {vhost_name}: {slugs}"
            )
            return slugs

        except (ImportError, ModuleNotFoundError):
            logger.debug(
                "Organization model not available. Running in organization-service mode (no database)."
            )

            if exclude:
                logger.info(
                    f"[ORGANIZATION-SERVICE] Excluding {org_slug}: returning empty list (no other orgs tracked)"
                )
                return []
            else:
                slugs = [org_slug] if org_slug else []
                logger.info(
                    f"[ORGANIZATION-SERVICE] Using org_slug for vhost {vhost_name}: {slugs}"
                )
                return slugs

        except Exception as e:
            logger.warning(
                f"Failed to retrieve organization slugs for vhost {vhost_name}: {e}"
            )
            if exclude:
                return []
            else:
                return [org_slug] if org_slug else []

    def provision_tenant(
        self, org_id: str, org_slug: str, vhost_number: int = None
    ) -> Dict:
        """
        Complete tenant provisioning workflow with load balancing

        Uses shared vhost pools to distribute load across vhosts.
        Picks the least-loaded vhost or creates a new one if all are full.

        Args:
            org_slug: Organization slug name
            org_id: Organization ID

        Returns:
            Dict with provisioning details (vhost, status)
        """
        exchange_name = f"{org_slug}.exchange"
        transformer_queue = f"{org_slug}.transformer.queue"
        transformed_data_queue = f"{org_slug}.transformed.data.queue"

        # Use shared default user from settings
        shared_username = settings.RABBITMQ_DEFAULT_USER

        try:
            logger.info(f"Starting tenant provisioning for: {org_slug}")

            # Find least-loaded vhost or create new one
            vhost_name = self.get_least_loaded_vhost()
            if not vhost_name:
                # Currently I just set random number based on time for uniqueness (Testing)
                # All vhosts are full or none exist, create new pool vhost
                if vhost_number is None:
                    vhost_number = int(time.time() % 10000)
                vhost_name = f"{self.VHOST_PREFIX}{vhost_number}"

                logger.info(f"Creating new tenant pool vhost: {vhost_name}")
                self.create_vhost(vhost_name)

            else:
                logger.info(f"Using existing vhost: {vhost_name}")

            # Always ensure shared user has permissions on the selected vhost
            self.set_permissions(vhost_name, shared_username)

            # Create exchange for this organization
            self.create_exchange(vhost_name, exchange_name)

            # Create queues
            self.create_queue(vhost_name, transformer_queue)
            self.create_queue(vhost_name, transformed_data_queue)

            # Bind amq.topic -> org exchange (for incoming device data)
            self.create_exchange_binding(
                vhost_name, "amq.topic", exchange_name, f"tenant.{org_slug}.device.data"
            )

            # Bind org exchange -> transformer queue
            self.create_binding(
                vhost_name,
                exchange_name,
                transformer_queue,
                f"tenant.{org_slug}.device.data",
            )

            # Bind org exchange -> transformed data queue
            self.create_binding(
                vhost_name,
                exchange_name,
                transformed_data_queue,
                f"tenant.{org_slug}.transformed.device.location",
            )

            self.create_binding(
                vhost_name,
                exchange_name,
                transformed_data_queue,
                f"tenant.{org_slug}.space.*.entity.*.telemetry",
            )

            logger.info(f"Successfully provisioned tenant: {org_slug}")

            try:
                emqx_client = EMQXClient()
                connector_name = emqx_client.ensure_connector(
                    vhost=vhost_name,
                    rabbit_user=settings.RABBITMQ_DEFAULT_USER,
                    rabbit_pass=settings.RABBITMQ_DEFAULT_PASSWORD,
                )
                emqx_client.ensure_vhost_action(vhost_name, connector_name)

                # Get organization slugs - handles both organization-service and console-service
                existing_slugs = [org_slug]  # Default: just current org
                try:
                    from apps.organization.models import Organization

                    # If model exists, query for all organizations on this vhost
                    existing_slugs = list(
                        Organization.objects.filter(
                            rabbitmq_vhost=vhost_name
                        ).values_list("slug_name", flat=True)
                    )
                    if org_slug not in existing_slugs:
                        existing_slugs.append(org_slug)
                    logger.debug(
                        f"[CONSOLE-SERVICE] Retrieved slugs from database: {existing_slugs}"
                    )
                except (ImportError, ModuleNotFoundError):
                    logger.debug(
                        f"[ORGANIZATION-SERVICE] Organization model not available, using current slug: {existing_slugs}"
                    )

                emqx_client.ensure_vhost_rule(vhost_name, existing_slugs)
            except Exception as e:
                logger.error(
                    f"Failed to configure EMQX resources for org {org_slug}: {str(e)}"
                )

            return {
                "vhost": vhost_name,
                "amqp_url": self.build_tenant_amqp_url(vhost_name),
                "exchange": exchange_name,
                "transformer_queue": transformer_queue,
                "transformed_queue": transformed_data_queue,
                "org_id": org_id,
                "org_slug": org_slug,
                "status": "provisioned",
            }
        except RabbitMQProvisionerError:
            logger.error(f"Tenant provisioning failed for: {org_slug}, rolling back")
            if vhost_name:
                self.delete_tenant(vhost_name, org_slug)  # Cleanup on failure
            raise

    def delete_tenant(self, vhost_name: str, org_slug: str = None) -> bool:
        """
        Delete tenant resources from shared vhost (load-balanced version)

        Deletes only the organization's exchanges and queues, NOT the shared vhost.

        Args:
            vhost_name: Vhost name containing the tenant resources
            org_slug: Organization slug to identify resources to delete
        """
        try:
            if not org_slug:
                logger.warning("No org_slug provided, cannot delete specific resources")
                return False

            # Delete organization-specific resources only
            exchange_name = f"{org_slug}.exchange"
            transformer_queue = f"{org_slug}.transformer.queue"
            transformed_data_queue = f"{org_slug}.transformed.data.queue"
            encoded_vhost = self._encode(vhost_name)

            # Delete queues
            for queue_name in [transformer_queue, transformed_data_queue]:
                try:
                    encoded_queue = self._encode(queue_name)
                    response = self.session.delete(
                        f"{self.api_url}/api/queues/{encoded_vhost}/{encoded_queue}"
                    )
                    response.raise_for_status()
                    logger.info(f"Deleted queue: {queue_name} from {vhost_name}")
                except requests.RequestException as e:
                    logger.warning(f"Failed to delete queue {queue_name}: {e}")

            # Delete exchange
            try:
                encoded_exchange = self._encode(exchange_name)
                response = self.session.delete(
                    f"{self.api_url}/api/exchanges/{encoded_vhost}/{encoded_exchange}"
                )
                response.raise_for_status()
                logger.info(f"Deleted exchange: {exchange_name} from {vhost_name}")
            except requests.RequestException as e:
                logger.warning(f"Failed to delete exchange {exchange_name}: {e}")

            logger.info(f"Kept shared vhost: {vhost_name} (used by other tenants)")

            try:
                emqx_client = EMQXClient()
                # Get remaining organization slugs - handles both organization-service and console-service
                remaining_slugs = []  # Default: no other slugs
                try:
                    from apps.organization.models import Organization

                    # If model exists, query for other organizations on this vhost
                    remaining_slugs = list(
                        Organization.objects.filter(rabbitmq_vhost=vhost_name)
                        .exclude(slug_name=org_slug)
                        .values_list("slug_name", flat=True)
                    )
                except (ImportError, ModuleNotFoundError):
                    logger.debug(
                        "Organization model not available, using empty slugs list"
                    )

                emqx_client.teardown_tenant(vhost_name, remaining_slugs)
            except Exception as e:
                logger.warning(
                    f"Failed to teardown EMQX resources for org {org_slug}: {str(e)}"
                )

            return True
        except Exception as e:
            logger.error(f"Failed to delete tenant resources: {e}")
            return False
