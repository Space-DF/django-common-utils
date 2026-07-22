"""DRF quota policies, similar to permission_classes.

Usage::

    from common.apps.billing.constants import FeatureCode

    class DeviceQuota(BaseQuota):
        rules = {
            "create": FeatureCode.DEVICE_MAX_COUNT,
            "bulk_create": FeatureCode.DEVICE_MAX_COUNT,
        }

    class DeviceViewSet(QuotaMixin, viewsets.ModelViewSet):
        quota_classes = [DeviceQuota]

Rules can use a single feature code, a list of feature codes, or scoped rule
objects like ``{"feature": FeatureCode.DEVICE_MAX_COUNT, "scope": scope}``.
"""

import logging

from rest_framework.exceptions import PermissionDenied

from common.apps.billing.constants import FeatureUsageScope
from common.apps.space.models import Space
from common.utils.console_client import console_client

logger = logging.getLogger(__name__)


class BaseQuota:
    rules = {}
    scope = FeatureUsageScope.USER
    feature_scopes = {}
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
        rule = self.rules.get(action)
        if rule is not None:
            return rule

        for actions, rule in self.rules.items():
            if isinstance(actions, (tuple, frozenset)) and action in actions:
                return rule

        return None

    def _normalize_rule_item(self, item):
        if isinstance(item, str):
            return {
                "feature": item,
                "scope": self.feature_scopes.get(item, self.scope),
            }

        if isinstance(item, dict):
            if "feature" in item:
                feature = item["feature"]
                return {
                    "feature": feature,
                    "scope": item.get(
                        "scope",
                        self.feature_scopes.get(feature, self.scope),
                    ),
                }

            return [
                {
                    "feature": feature,
                    "scope": scope,
                }
                for feature, scope in item.items()
            ]

        if isinstance(item, (list, tuple)) and len(item) == 2:
            return {
                "feature": item[0],
                "scope": item[1],
            }

        return None

    def get_feature_rules(self, request, view):
        rule = self.get_rule(request, view)
        if not rule:
            return []

        items = rule if isinstance(rule, list) else [rule]
        feature_rules = []

        for item in items:
            normalized = self._normalize_rule_item(item)
            if normalized is None:
                continue
            if isinstance(normalized, list):
                feature_rules.extend(normalized)
            else:
                feature_rules.append(normalized)

        deduped_rules = []
        seen = set()
        for feature_rule in feature_rules:
            key = (feature_rule["feature"], feature_rule["scope"])
            if key in seen:
                continue
            seen.add(key)
            deduped_rules.append(feature_rule)

        return deduped_rules

    def get_features(self, request, view):
        feature_rules = self.get_feature_rules(request, view)
        if not feature_rules:
            return []

        features = [feature_rule["feature"] for feature_rule in feature_rules]
        return list(dict.fromkeys(features))

    def get_org_slug(self, request, view):
        tenant = getattr(request, "tenant", None)
        return getattr(tenant, "slug_name", None) or request.headers.get(
            "X-Organization"
        )

    def get_user_id(self, request, view):
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id

        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            return getattr(user, "id", None)
        return None

    def get_scope_id(self, request, view, scope_type):
        if scope_type == FeatureUsageScope.ORGANIZATION:
            return None
        if scope_type == FeatureUsageScope.USER:
            return self.get_user_id(request, view)
        if scope_type == FeatureUsageScope.SPACE:
            space_slug = request.headers.get("X-Space")
            if not space_slug:
                return None

            return (
                Space.objects.filter(slug_name=space_slug)
                .values_list("id", flat=True)
                .first()
            )
        return None

    def get_feature_scope(self, request, view, feature):
        return self.feature_scopes.get(feature, self.scope)

    def _group_features_by_scope(self, request, view, feature_rules):
        grouped_features = {}

        for feature_rule in feature_rules:
            feature = feature_rule["feature"]
            scope_type = feature_rule["scope"]
            scope_id = self.get_scope_id(request, view, scope_type)
            if scope_type != FeatureUsageScope.ORGANIZATION and not scope_id:
                self.message = f"Scope id is required for quota scope '{scope_type}'."
                return None

            grouped_features.setdefault((scope_type, scope_id), []).append(feature)

        return grouped_features

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
                reservation["scope_type"],
                reservation["scope_id"],
                reservation["feature"],
                reservation["amount"],
            )
            if key in released:
                continue

            group_key = (
                reservation["org_slug"],
                reservation["scope_type"],
                reservation["scope_id"],
                reservation["amount"],
            )
            grouped_features.setdefault(group_key, []).append(reservation["feature"])
            released.add(key)

        for (
            org_slug,
            scope_type,
            scope_id,
            reserved_amount,
        ), features in grouped_features.items():
            for feature in features:
                try:
                    console_client.release_quota(
                        org_slug,
                        feature,
                        reserved_amount,
                        scope_type=scope_type,
                        scope_id=scope_id,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning("release_quota failed for %s/%s", org_slug, feature)

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
        feature_rules = self.get_feature_rules(request, view)
        if not feature_rules:
            return True

        org_slug = self.get_org_slug(request, view)
        if not org_slug:
            return True

        grouped_features = self._group_features_by_scope(request, view, feature_rules)
        if grouped_features is None:
            return False

        for (scope_type, scope_id), scoped_features in grouped_features.items():
            for feature in scoped_features:
                reserved, error = console_client.reserve_quota(
                    org_slug,
                    feature,
                    amount,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
                if not reserved:
                    self.message = error or self.message
                    self.release(request, view)
                    return False

                if amount > 0:
                    view._quota_reserved.append(
                        {
                            "quota": self,
                            "org_slug": org_slug,
                            "scope_type": scope_type,
                            "scope_id": scope_id,
                            "feature": feature,
                            "amount": amount,
                        }
                    )

        return True

    def _release_features(self, request, view, amount):
        feature_rules = self.get_feature_rules(request, view)
        if not feature_rules:
            return None

        org_slug = self.get_org_slug(request, view)
        if not org_slug:
            return None

        grouped_features = self._group_features_by_scope(request, view, feature_rules)
        if grouped_features is None:
            return None

        for (scope_type, scope_id), scoped_features in grouped_features.items():
            for feature in scoped_features:
                try:
                    console_client.release_quota(
                        org_slug,
                        feature,
                        amount,
                        scope_type=scope_type,
                        scope_id=scope_id,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "release_quota failed for %s/%s",
                        org_slug,
                        feature,
                    )

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
