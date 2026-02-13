from common.apps.space_role.constants import SpacePermission
from django.db import migrations

default_policies = [
    {
        "name": "Administrator access",
        "description": "Provides full access to services and resources",
        "tags": ["administrator"],
        "permissions": [permission.value for permission in SpacePermission],
    },
    {
        "name": "Space full access",
        "description": "Grants full access to Space resources and access to related services",
        "tags": ["space", "full access"],
        "permissions": [
            SpacePermission.UPDATE_SPACE,
            SpacePermission.DELETE_SPACE,
        ],
    },
    {
        "name": "Space's Role read-only access",
        "description": "Provide read only access to Space's Role services",
        "tags": ["space-role", "read-only"],
        "permissions": [
            SpacePermission.READ_SPACE_ROLE,
        ],
    },
    {
        "name": "Space's Role full access",
        "description": "Grants full access to Space's Role resources and access to related services",
        "tags": ["space-role", "full-access"],
        "permissions": [
            SpacePermission.READ_SPACE_ROLE,
            SpacePermission.CREATE_SPACE_ROLE,
            SpacePermission.UPDATE_SPACE_ROLE,
            SpacePermission.DELETE_SPACE_ROLE,
        ],
    },
    {
        "name": "Space's Member read-only access",
        "description": "Provide read only access to Space's Member services",
        "tags": ["space-member", "read-only"],
        "permissions": [
            SpacePermission.READ_SPACE_MEMBER,
        ],
    },
    {
        "name": "Space's Member full access",
        "description": "Grants full access to Space's Member resources and access to related services",
        "tags": ["space-member", "full-access"],
        "permissions": [
            SpacePermission.READ_SPACE_MEMBER,
            SpacePermission.INVITE_SPACE_MEMBER,
            SpacePermission.UPDATE_SPACE_MEMBER_ROLE,
            SpacePermission.REMOVE_SPACE_MEMBER,
        ],
    },
    {
        "name": "Dashboard read-only access",
        "description": "Provide read only access to Dashboard services",
        "tags": ["dashboard", "read-only"],
        "permissions": [
            SpacePermission.READ_DASHBOARD,
            SpacePermission.READ_DEVICE_STATE,
        ],
    },
    {
        "name": "Dashboard full access",
        "description": "Grants full access to Dashboard resources and access to related services",
        "tags": ["dashboard", "full-access"],
        "permissions": [
            SpacePermission.READ_DASHBOARD,
            SpacePermission.CREATE_DASHBOARD,
            SpacePermission.UPDATE_DASHBOARD,
            SpacePermission.DELETE_DASHBOARD,
            SpacePermission.READ_DEVICE_STATE,
        ],
    },
]


def create_default_policy(apps, schema_editor):
    SpacePolicy = apps.get_model("space_role", "SpacePolicy")

    for policy in default_policies:
        SpacePolicy(**policy).save()


class Migration(migrations.Migration):
    dependencies = [
        ("space_role", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_default_policy)]
