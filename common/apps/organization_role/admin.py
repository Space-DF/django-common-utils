from common.apps.organization_role.models import (
    OrganizationPolicy,
    OrganizationRole,
    OrganizationRoleUser,
)
from django.contrib import admin


@admin.register(OrganizationPolicy)
class OrganizationPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "tags",
        "actions",
        "created_at",
        "updated_at",
    )


@admin.register(OrganizationRole)
class OrganizationRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "created_at",
        "updated_at",
    )


@admin.register(OrganizationRoleUser)
class OrganizationRoleUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "organization_role",
        "organization_user",
        "created_at",
        "updated_at",
    )
