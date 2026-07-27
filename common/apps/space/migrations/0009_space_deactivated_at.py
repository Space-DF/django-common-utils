from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("space", "0008_space_is_deactivated"),
    ]

    operations = [
        migrations.AddField(
            model_name="space",
            name="deactivated_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
