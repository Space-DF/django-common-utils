from rest_framework import serializers


class DynamicSerializerMixin:
    """
    A Serializer that takes additional `fields` and `exclude` arguments.
    - `fields`: Controls which fields should be included.
    - `exclude`: Controls which fields should be excluded.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

        if exclude is not None:
            excluded = set(exclude)
            for field_name in excluded:
                self.fields.pop(field_name, None)


class DynamicFieldsSerializer(DynamicSerializerMixin, serializers.Serializer):
    pass


class DynamicModelSerializer(DynamicSerializerMixin, serializers.ModelSerializer):
    pass
