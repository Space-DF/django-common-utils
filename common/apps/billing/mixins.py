"""DRF mixin enforcing plan quota via the reserve-then-create pattern.

Usage::

    class DeviceViewSet(QuotaMixin, viewsets.ModelViewSet):
        feature = "device.max_count"

Flow per request:
1. On ``create`` action, ``initial()`` calls Console to reserve ``amount`` units.
2. If reserve fails (403), the request is denied with ``PermissionDenied``.
3. If reserve succeeds, the view runs normally.
4. If the view's ``perform_create`` raises, the reservation is released so the quota doesn't leak.

Fail-open: if Console is unreachable or returns an unexpected status, the
request is allowed — billing infra problems must not block the core product.
"""

import logging

from rest_framework.exceptions import PermissionDenied

from common.utils.console_client import console_client

logger = logging.getLogger(__name__)


class QuotaMixin:
    # Plan feature this view enforces (e.g. "device.max_count").
    # Leave as None to opt this view out of quota enforcement.
    feature = None

    def get_amount(self, request) -> int:
        """Number of units to reserve per create. Override for bulk operations."""
        return 1

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if not self.feature or self.action != "create":
            return

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return

        org_slug = getattr(tenant, "slug_name", None)
        if not org_slug:
            return

        amount = self.get_amount(request)
        reserved, error = console_client.reserve_quota(org_slug, self.feature, amount)
        if not reserved:
            raise PermissionDenied(error or "Quota exceeded.")

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception:
            tenant = getattr(self.request, "tenant", None)
            if tenant:
                org_slug = getattr(tenant, "slug_name", None)
                if org_slug:
                    amount = self.get_amount(self.request)
                    try:
                        console_client.release_quota(org_slug, self.feature, amount)
                    except Exception:  # noqa: BLE001
                        logger.warning(
                            "release_quota failed for %s/%s",
                            org_slug,
                            self.feature,
                        )
            raise
