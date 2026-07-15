"""Shared downgrade consumer for Python services.

Each service plugs in its own deactivation callback and queue name.
Declares a NAMED, DURABLE queue — messages survive consumer restarts.

"""

import json
import logging
import time as _time

import pika
from django.conf import settings

logger = logging.getLogger(__name__)

_RECONNECT_DELAY = 5


def run_downgrade_consumer(queue_name, callback):
    """Blocking — connects to RabbitMQ, listens for ``org.downgraded`` events.

    Declares a durable named queue so messages are not lost if the
    consumer is restarted. The queue declaration is idempotent —
    RabbitMQ ignores duplicate declarations with the same parameters.

    Args:
        queue_name: Durable queue name (e.g. ``device.org.events.queue``).
        callback: ``callable(organization_slug: str)`` — called per message.
    """
    exchange = getattr(settings, "ORG_EVENTS_EXCHANGE", "org.events")
    rabbitmq_url = _resolve_rabbitmq_url()

    params = pika.URLParameters(rabbitmq_url)

    while True:
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(
                exchange=exchange, exchange_type="topic", durable=True
            )

            channel.queue_declare(
                queue=queue_name, durable=True, exclusive=False, auto_delete=False
            )
            channel.queue_bind(
                exchange=exchange, queue=queue_name, routing_key="org.downgraded"
            )

            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=_make_handler(callback),
            )

            logger.info(
                "Downgrade consumer started (queue=%s, exchange=%s)",
                queue_name,
                exchange,
            )
            channel.start_consuming()
        except Exception:
            logger.exception(
                "Downgrade consumer error (queue=%s), reconnecting in %ss...",
                queue_name,
                _RECONNECT_DELAY,
            )
            _time.sleep(_RECONNECT_DELAY)


def _make_handler(callback):
    def _handle(channel, method, _properties, body):
        try:
            envelope = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("Invalid downgrade message payload, acking")
            channel.basic_ack(delivery_tag=method.delivery_tag)
            return

        inner = envelope.get("payload", {})
        org_slug = inner.get("slug")
        limits = inner.get("limits", {})
        try:
            if org_slug:
                callback(org_slug, limits=limits)
        except Exception:
            logger.exception("Deactivation callback failed for org %s", org_slug)
        finally:
            channel.basic_ack(delivery_tag=method.delivery_tag)

    return _handle


def _resolve_rabbitmq_url():
    return getattr(
        settings,
        "CELERY_BROKER_URL",
        getattr(settings, "RABBITMQ_URL", "amqp://guest:guest@localhost"),
    )
