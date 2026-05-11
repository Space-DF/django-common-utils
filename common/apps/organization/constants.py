
from django.db import models


class OrganizationTemplate(models.TextChoices):
    SMART_BUILDING = "smart_building"
    SMART_FLEET_MONITOR = "smart_fleet_monitor"
