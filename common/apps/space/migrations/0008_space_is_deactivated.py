# Generated manually — adds is_deactivated field to Space model

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("space", "0007_remove_space_build_artifact"),
    ]

    operations = [
        migrations.AddField(
            model_name="space",
            name="is_deactivated",
            field=models.BooleanField(default=False),
        ),
    ]
