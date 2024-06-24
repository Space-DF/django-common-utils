from drf_yasg.renderers import _SpecRenderer
from drf_yasg.views import get_schema_view
from rest_framework import exceptions
from rest_framework.response import Response


def get_tenant_schema_view(
    info=None,
    path=None,
    patterns=None,
    urlconf=None,
    public=False,
    validators=None,
    generator_class=None,
    authentication_classes=None,
    permission_classes=None,
):
    SchemaView = get_schema_view(
        info=info,
        url="localhost",
        patterns=patterns,
        urlconf=urlconf,
        public=public,
        validators=validators,
        generator_class=generator_class,
        authentication_classes=authentication_classes,
        permission_classes=permission_classes,
    )

    class TenantSchemaView(SchemaView):
        def get(self, request, version="", format=None):
            url = "{0}://{1}{2}".format(request.scheme, request.get_host(), path)
            version = request.version or version or ""
            if isinstance(request.accepted_renderer, _SpecRenderer):
                generator = self.generator_class(info, version, url, patterns, urlconf)
            else:
                generator = self.generator_class(info, version, url, patterns=[])

            schema = generator.get_schema(request, self.public)
            if schema is None:
                raise exceptions.PermissionDenied()  # pragma: no cover
            return Response(schema)

    return TenantSchemaView
