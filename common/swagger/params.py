from drf_yasg import openapi


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
