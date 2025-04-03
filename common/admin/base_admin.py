from django.contrib import admin


class ListDisplayMixin(admin.ModelAdmin):
    list_display_exclude = ()

    def get_list_display(self, request):
        all_fields = [field.name for field in self.model._meta.fields]
        list_display = [
            field for field in all_fields if field not in self.list_display_exclude
        ]
        return list_display
