from common.apps.space_role.models import SpacePolicy, SpaceRole, SpaceRoleUser
from django.contrib import admin


@admin.register(SpacePolicy)
class SpacePolicyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "tags",
        "actions",
        "created_at",
        "updated_at",
    )


@admin.register(SpaceRole)
class SpaceRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "space",
        "created_at",
        "updated_at",
    )


@admin.register(SpaceRoleUser)
class SpaceRoleUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "space_role",
        "organization_user",
        "created_at",
        "updated_at",
    )
