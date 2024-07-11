from common.apps.space_role.models import SpacePolicy, SpaceRole


def create_default_role_by_policy_tag(space, name, tag):
    policies = SpacePolicy.objects.filter(tags__icontains=tag).all()
    space_role = SpaceRole(name=name, space=space)
    space_role.save()

    SpaceRolePolicy = SpaceRole.policies.through
    SpaceRolePolicy.objects.bulk_create(
        [
            SpaceRolePolicy(spacerole_id=space_role.pk, spacepolicy_id=policy.pk)
            for policy in policies
        ]
    )

    return space_role


def create_space_default_role(space):
    owner_role = create_default_role_by_policy_tag(space, "Owner", "administrator")
    reader_role = create_default_role_by_policy_tag(space, "Reader", "read-only")

    return owner_role, reader_role
