from common.apps.space_role.models import SpacePolicy, SpaceRole, SpaceRoleUser
from common.celery.tasks import create_tenant_model_shared_tasks

update_space_policy, delete_space_policy = create_tenant_model_shared_tasks(SpacePolicy)
update_space_role, delete_space_role = create_tenant_model_shared_tasks(SpaceRole)
update_space_role_user, delete_space_role_user = create_tenant_model_shared_tasks(
    SpaceRoleUser
)
