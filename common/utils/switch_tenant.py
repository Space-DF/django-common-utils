from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django_tenants.utils import get_tenant_domain_model
from rest_framework import status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.response import Response


class UseTenantFromRequestMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        org_param = request.query_params.get("organization", None)
        if org_param is not None:
            organization = org_param
            if organization == "":
                return Response({"result": "deny"}, status=status.HTTP_200_OK)
        else:
            organization = request.headers.get("X-Organization")

        if not organization:
            raise ParseError("Missing 'organization' parameter")

        domain_model = get_tenant_domain_model()
        try:
            domain = domain_model.objects.select_related("tenant").get(
                tenant__schema_name=organization
            )
            tenant = domain.tenant
        except ObjectDoesNotExist:
            raise NotFound(f"Tenant '{organization}' not found")

        connection.set_tenant(tenant)
        request.tenant = tenant
