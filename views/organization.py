from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView

from pkg.swagger.params import get_organization_header_params


class OrganizationAPIView(GenericAPIView):
    organization_field = None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.organization_field is None:
            raise Exception(
                "'%s' should either include a `organization_field` attribute, or override the `get_queryset()` method."
                % self.__class__.__name__
            )

        organization_slug_name = self.request.headers.get("organization", None)
        if organization_slug_name is None:
            raise ParseError("organization is required")

        filters = {
            f"{self.organization_field}__slug_name": organization_slug_name,
            f"{self.organization_field}__is_active": True,
        }

        return queryset.filter(**filters)


class OrganizationCreateAPIView(mixins.CreateModelMixin, OrganizationAPIView):
    """
    Concrete view for creating a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class OrganizationListAPIView(mixins.ListModelMixin, OrganizationAPIView):
    """
    Concrete view for listing a queryset of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class OrganizationRetrieveAPIView(mixins.RetrieveModelMixin, OrganizationAPIView):
    """
    Concrete view for retrieving a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class OrganizationDestroyAPIView(mixins.DestroyModelMixin, OrganizationAPIView):
    """
    Concrete view for deleting a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class OrganizationUpdateAPIView(mixins.UpdateModelMixin, OrganizationAPIView):
    """
    Concrete view for updating a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class OrganizationListCreateAPIView(
    mixins.ListModelMixin, mixins.CreateModelMixin, OrganizationAPIView
):
    """
    Concrete view for listing a queryset or creating a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class OrganizationRetrieveUpdateAPIView(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, OrganizationAPIView
):
    """
    Concrete view for retrieving, updating a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class OrganizationRetrieveDestroyAPIView(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, OrganizationAPIView
):
    """
    Concrete view for retrieving or deleting a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class OrganizationRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    OrganizationAPIView,
):
    """
    Concrete view for retrieving, updating or deleting a model instance of organization.
    """

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_organization_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
