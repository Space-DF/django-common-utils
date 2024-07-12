from common.apps.organization_role.models import (
    OrganizationPolicy,
    OrganizationRole,
    OrganizationRoleUser,
)
from common.celery.tasks import create_tenant_model_shared_tasks

(
    update_organization_policy,
    delete_organization_policy,
) = create_tenant_model_shared_tasks(OrganizationPolicy)
update_organization_role, delete_organization_role = create_tenant_model_shared_tasks(
    OrganizationRole
)
(
    update_organization_role_user,
    delete_organization_role_user,
) = create_tenant_model_shared_tasks(OrganizationRoleUser)
