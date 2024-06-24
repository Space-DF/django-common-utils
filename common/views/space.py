from common.swagger.params import get_space_header_params
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins
from rest_framework.exceptions import ParseError
from rest_framework.generics import GenericAPIView


class SpaceAPIView(GenericAPIView):
    space_field = None

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.space_field is None:
            raise Exception(
                "'%s' should either include a `space_field` attribute, or override the `get_queryset()` method."
                % self.__class__.__name__
            )

        space_slug_name = self.request.headers.get("space", None)
        if space_slug_name is None:
            raise ParseError("space is required")

        filters = {
            f"{self.space_field}__slug_name": space_slug_name,
            f"{self.space_field}__is_active": True,
        }

        return queryset.filter(**filters)


class SpaceCreateAPIView(mixins.CreateModelMixin, SpaceAPIView):
    """
    Concrete view for creating a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class SpaceListAPIView(mixins.ListModelMixin, SpaceAPIView):
    """
    Concrete view for listing a queryset of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SpaceRetrieveAPIView(mixins.RetrieveModelMixin, SpaceAPIView):
    """
    Concrete view for retrieving a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class SpaceDestroyAPIView(mixins.DestroyModelMixin, SpaceAPIView):
    """
    Concrete view for deleting a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class SpaceUpdateAPIView(mixins.UpdateModelMixin, SpaceAPIView):
    """
    Concrete view for updating a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class SpaceListCreateAPIView(
    mixins.ListModelMixin, mixins.CreateModelMixin, SpaceAPIView
):
    """
    Concrete view for listing a queryset or creating a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class SpaceRetrieveUpdateAPIView(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, SpaceAPIView
):
    """
    Concrete view for retrieving, updating a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class SpaceRetrieveDestroyAPIView(
    mixins.RetrieveModelMixin, mixins.DestroyModelMixin, SpaceAPIView
):
    """
    Concrete view for retrieving or deleting a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class SpaceRetrieveUpdateDestroyAPIView(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    SpaceAPIView,
):
    """
    Concrete view for retrieving, updating or deleting a model instance of space.
    """

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @swagger_auto_schema(manual_parameters=get_space_header_params())
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
