from rest_framework.exceptions import PermissionDenied


class DeactivationMixin:
    deactivation = None
    deactivation_lookup_model = None
    deactivation_lookup_kwarg = None
    deactivation_lookup_field = "pk"
    deactivation_lookup_select_related = None

    def _is_self_reference(self, target, attr):
        model_meta = getattr(target, "_meta", None)
        model_name = getattr(model_meta, "model_name", None)
        class_name = (
            target.__name__.lower()
            if isinstance(target, type)
            else target.__class__.__name__.lower()
        )
        return attr in {model_name, class_name}

    def _resolve_target(self, instance, target_path):
        target = instance
        if target_path:
            for attr in target_path.split("."):
                if target is None:
                    break
                if self._is_self_reference(target, attr):
                    continue
                target = getattr(target, attr, None)
        return target

    def _get_deactivation_targets(self, instance):
        if not self.deactivation:
            return [(None, instance)]
        return [
            (target_path, self._resolve_target(instance, target_path))
            for target_path in self.deactivation
        ]

    def _get_view_model(self):
        model = getattr(self, "model", None)
        if model:
            return model

        queryset = getattr(self, "queryset", None)
        return getattr(queryset, "model", None)

    def _get_deactivation_root(self):
        if not self.deactivation:
            return None
        return self.deactivation[0].split(".")[0]

    def _get_deactivation_lookup_model(self):
        if self.deactivation_lookup_model:
            return self.deactivation_lookup_model

        root = self._get_deactivation_root()
        view_model = self._get_view_model()
        if not root or not view_model:
            return None

        if self._is_self_reference(view_model, root):
            return view_model

        try:
            field = view_model._meta.get_field(root)
        except Exception:
            return None
        return getattr(field.remote_field, "model", None)

    def _get_deactivation_lookup_kwarg(self, lookup_model):
        if self.deactivation_lookup_kwarg:
            return self.deactivation_lookup_kwarg

        root = self._get_deactivation_root()
        if root:
            related_kwarg = f"{root}_id"
            if related_kwarg in self.kwargs:
                return related_kwarg

        if lookup_model and root and self._is_self_reference(lookup_model, root):
            lookup_kwarg = getattr(self, "lookup_url_kwarg", None)
            lookup_field = getattr(self, "lookup_field", None)
            for candidate in (lookup_kwarg, lookup_field, "pk", "id"):
                if candidate and candidate in self.kwargs:
                    return candidate

        return None

    def get_deactivation_message(self, target, target_path=None):
        model_meta = getattr(target, "_meta", None)
        label = getattr(model_meta, "verbose_name", None)
        if not label and target_path:
            label = target_path.split(".")[-1].replace("_", " ")
        if not label:
            label = "Object"
        return f"{label.title()} is deactivated."

    def check_deactivated(self, target, target_path=None):
        if target and getattr(target, "is_deactivated", False):
            raise PermissionDenied(self.get_deactivation_message(target, target_path))

    def check_deactivated_object(self, instance):
        for target_path, target in self._get_deactivation_targets(instance):
            self.check_deactivated(target, target_path)
        return instance

    def get_deactivation_lookup_object(self):
        lookup_model = self._get_deactivation_lookup_model()
        lookup_kwarg = self._get_deactivation_lookup_kwarg(lookup_model)
        if not lookup_model or not lookup_kwarg:
            return None

        lookup_value = self.kwargs.get(lookup_kwarg)
        if not lookup_value:
            return None

        queryset = lookup_model.objects.all()
        if self.deactivation_lookup_select_related:
            queryset = queryset.select_related(*self.deactivation_lookup_select_related)

        return queryset.filter(**{self.deactivation_lookup_field: lookup_value}).first()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        instance = self.get_deactivation_lookup_object()
        if instance:
            self.check_deactivated_object(instance)

    def get_object(self):
        instance = super().get_object()
        return self.check_deactivated_object(instance)
