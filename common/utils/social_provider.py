from django.db import models


class SocialProvider(models.TextChoices):
    GOOGLE = "google"
    NONE_PROVIDER = None
