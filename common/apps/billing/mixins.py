"""DRF mixin enforcing plan quota via the reserve-then-create pattern.

Usage::

    class DeviceViewSet(QuotaMixin, viewsets.ModelViewSet):
        feature = "device.max_count"

Flow per request:
1. On POST, ``initial()`` calls Console to reserve ``amount`` units.
2. If reserve fails (403), the request is denied with ``PermissionDenied``.
3. If reserve succeeds, the view runs normally.
4. If the view's ``perform_create`` raises, the reservation is released so the quota doesn't leak.

Fail-open: if Console is unreachable or returns an unexpected status, the
request is allowed — billing infra problems must not block the core product.
"""

import logging

from rest_framework.exceptions import PermissionDenied

from common.utils.console_client import ConsoleServiceClient

logger = logging.getLogger(__name__)


class QuotaMixin:
    # Plan feature this view enforces (e.g. "device.max_count").
    # Leave as None to opt this view out of quota enforcement.
    feature = None
    # Number of units to reserve per create. Override for bulk operations.
    amount = 1

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        if not self.feature or request.method != "POST":
            return  # only enforce on create

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return

        # Use slug_name instead of schema_name for organization lookup
        org_slug = getattr(tenant, "slug_name", None)
        if not org_slug:
            return

        reserved, error = ConsoleServiceClient().reserve_quota(
            org_slug, self.feature, self.amount
        )
        if not reserved:
            raise PermissionDenied(error or "Quota exceeded.")

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception:
            # Release the reservation since the create failed.
            tenant = getattr(self.request, "tenant", None)
            if tenant:
                org_slug = getattr(tenant, "slug_name", None)
                if org_slug:
                    try:
                        ConsoleServiceClient().release_quota(
                            org_slug, self.feature, self.amount
                        )
                    except Exception:  # noqa: BLE001
                        logger.warning(
                            "release_quota failed for %s/%s",
                            org_slug,
                            self.feature,
                        )
            raise
