from drf_yasg import openapi
from drf_yasg.inspectors import SwaggerAutoSchema


def get_space_header_params(required=True):
    return [
        openapi.Parameter(
            name="X-Space",
            description="Space slug name",
            required=required,
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            default="",
        )
    ]


class CustomSwaggerAutoSchema(SwaggerAutoSchema):
    def get_operation(self, operation_keys=None):
        operation = super().get_operation(operation_keys)
        api_key_param = openapi.Parameter(
            name="x-api-key",
            in_=openapi.IN_HEADER,
            type=openapi.TYPE_STRING,
            required=True,
            description="API Key for authentication",
        )
        if any(
            path in self.path for path in ["api/health", "docs", "api/auth", "admin"]
        ):
            api_key_param["required"] = False

        operation["parameters"] = operation.get("parameters", []) + [api_key_param]
        return operation
