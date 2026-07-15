"""DRF quota policies, similar to permission_classes.

Usage::

    class DeviceQuota(BaseQuota):
        rules = {
            "create": "device.max_count",
            "bulk_create": "device.max_count",
            "list": "device.read_limit",
            "retrieve": "device.read_limit",
        }

    class DeviceViewSet(QuotaMixin, viewsets.ModelViewSet):
        quota_classes = [DeviceQuota]

Rules can use a single feature code or a list of feature codes.
"""

import logging

from rest_framework.exceptions import PermissionDenied

from common.utils.console_client import console_client

logger = logging.getLogger(__name__)


class BaseQuota:
    rules = {}
    reserve_actions = {"create", "bulk_create"}
    release_actions = set()
    method_action_map = {
        "GET": "retrieve",
        "POST": "create",
        "PUT": "update",
        "PATCH": "partial_update",
        "DELETE": "destroy",
    }
    message = "Quota exceeded."

    def get_action(self, request, view):
        action = getattr(view, "action", None)
        if action:
            return action
        return self.method_action_map.get(request.method.upper())

    def get_rule(self, request, view):
        action = self.get_action(request, view)
        if not action:
            return None
        return self.rules.get(action)

    def get_features(self, request, view):
        rule = self.get_rule(request, view)
        if not rule:
            return []
        if isinstance(rule, str):
            return [rule]
        return list(dict.fromkeys(rule))

    def get_org_slug(self, request, view):
        tenant = getattr(request, "tenant", None)
        return getattr(tenant, "slug_name", None)

    def get_amount(self, request, view):
        if hasattr(view, "get_quota_amount"):
            return view.get_quota_amount(request, self)
        if hasattr(view, "get_amount"):
            return view.get_amount(request)
        if isinstance(getattr(request, "data", None), list):
            return len(request.data)
        return 1

    def should_reserve(self, request, view):
        action = self.get_action(request, view)
        return action in self.reserve_actions

    def should_release(self, request, view):
        action = self.get_action(request, view)
        return action in self.release_actions

    def has_quota(self, request, view):
        return self._check_features(request, view, amount=0)

    def reserve(self, request, view, amount):
        return self._check_features(request, view, amount=amount)

    def release(self, request, view, amount=None):
        if amount is not None:
            return self._release_features(request, view, amount)

        grouped_features = {}
        released = getattr(view, "_quota_released", set())

        for reservation in getattr(view, "_quota_reserved", []):
            if reservation["quota"] is not self:
                continue

            key = (
                id(reservation["quota"]),
                reservation["org_slug"],
                reservation["feature"],
                reservation["amount"],
            )
            if key in released:
                continue

            group_key = (reservation["org_slug"], reservation["amount"])
            grouped_features.setdefault(group_key, []).append(reservation["feature"])
            released.add(key)

        for (org_slug, reserved_amount), features in grouped_features.items():
            try:
                console_client.release_quota(org_slug, features, reserved_amount)
            except Exception:  # noqa: BLE001
                logger.warning("release_quota failed for %s/%s", org_slug, features)

        view._quota_released = released
        return None

    def check(self, request, view):
        if self.should_reserve(request, view):
            amount = self.get_amount(request, view)
            return self.reserve(request, view, amount)
        if self.should_release(request, view):
            return True
        return self.has_quota(request, view)

    def _check_features(self, request, view, amount):
        features = self.get_features(request, view)
        if not features:
            return True

        org_slug = self.get_org_slug(request, view)
        if not org_slug:
            return True

        reserved, error = console_client.reserve_quota(org_slug, features, amount)
        if not reserved:
            self.message = error or self.message
            self.release(request, view)
            return False

        for feature in features:
            if amount > 0:
                view._quota_reserved.append(
                    {
                        "quota": self,
                        "org_slug": org_slug,
                        "feature": feature,
                        "amount": amount,
                    }
                )

        return True

    def _release_features(self, request, view, amount):
        features = self.get_features(request, view)
        if not features:
            return None

        org_slug = self.get_org_slug(request, view)
        if not org_slug:
            return None

        try:
            console_client.release_quota(org_slug, features, amount)
        except Exception:  # noqa: BLE001
            logger.warning("release_quota failed for %s/%s", org_slug, features)

        return None


class QuotaMixin:
    quota_classes = []

    def get_amount(self, request):
        if isinstance(getattr(request, "data", None), list):
            return len(request.data)
        return 1

    def get_quota_classes(self):
        return [quota_class() for quota_class in self.quota_classes]

    def check_quotas(self, request):
        for quota in self._quota_instances:
            if not quota.check(request, self):
                self.release_quotas(request)
                raise PermissionDenied(quota.message)

    def release_quotas(self, request):
        for quota in getattr(self, "_quota_instances", []):
            quota.release(request, self)

    def initial(self, request, *args, **kwargs):
        self._quota_reserved = []
        self._quota_released = set()
        self._quota_instances = self.get_quota_classes()

        super().initial(request, *args, **kwargs)
        self.check_quotas(request)

    def handle_exception(self, exc):
        self.release_quotas(self.request)
        return super().handle_exception(exc)

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except Exception:
            self.release_quotas(self.request)
            raise

    def perform_destroy(self, instance):
        super().perform_destroy(instance)

        for quota in getattr(self, "_quota_instances", []):
            if quota.should_release(self.request, self):
                quota.release(
                    self.request,
                    self,
                    amount=quota.get_amount(self.request, self),
                )
