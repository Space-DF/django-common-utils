import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class HexCharField(serializers.CharField):
    def __init__(self, length, unique=False, **kwargs):
        self.length = length
        self.format = re.compile(rf"^[a-fA-F0-9]{{{length}}}$")
        self.unique = unique
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)
        if self.unique and hasattr(parent.Meta, "model"):
            model = parent.Meta.model
            self.validators.append(
                UniqueValidator(
                    queryset=model.objects.all(),
                    message=f"Device with this {field_name} already exists.",
                )
            )

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value and not self.format.fullmatch(value):
            raise serializers.ValidationError(
                f"Value must be {self.length} hex characters"
            )
        return value
