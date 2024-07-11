from common.apps.space.models import Space
from django.contrib import admin


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "logo",
        "is_multi_tenant",
        "created_at",
        "updated_at",
    )
