from common.apps.organization.handler import NewOrganizationHandlerBase
from common.apps.organization_role.models import (
    OrganizationPolicy,
    OrganizationRole,
    OrganizationRoleUser,
)
from common.apps.organization_user.models import OrganizationUser
from common.apps.space.models import Space
from common.apps.space_role.models import SpaceRoleUser
from common.apps.space_role.services import create_space_default_role
from django.db import transaction
from django_tenants.utils import get_tenant_model, tenant_context


class NewOrganizationHandler(NewOrganizationHandlerBase):
    def create_default_organization_role_by_policy_tag(self, name, tag):
        policies = OrganizationPolicy.objects.filter(tags__icontains=tag).all()
        organization_role = OrganizationRole(name=name)
        organization_role.save()

        OrganizationRolePolicy = OrganizationRole.policies.through
        OrganizationRolePolicy.objects.bulk_create(
            [
                OrganizationRolePolicy(
                    organizationrole_id=organization_role.pk,
                    organizationpolicy_id=policy.pk,
                )
                for policy in policies
            ]
        )

        return organization_role

    @transaction.atomic()
    def handle(self):
        organization = get_tenant_model().objects.get(
            schema_name=self._organization.slug_name
        )
        with tenant_context(organization):
            # Create owner user
            owner = OrganizationUser(email=self._owner_email, is_owner=True)
            owner.save()

            # Create default space
            space = Space(
                name="default",
                logo=self._organization.logo,
                slug_name="default",
            )
            space.save()
            owner_role, _ = create_space_default_role(space)
            SpaceRoleUser(organization_user=owner, space_role=owner_role).save()

            owner_role = self.create_default_organization_role_by_policy_tag(
                "Owner", "administrator"
            )
            self.create_default_organization_role_by_policy_tag("Reader", "read-only")

            OrganizationRoleUser(
                organization_user=owner, organization_role=owner_role
            ).save()
