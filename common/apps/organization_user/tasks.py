from common.apps.organization_user.models import OrganizationUser
from common.celery.tasks import create_tenant_model_shared_tasks

update_space, delete_space = create_tenant_model_shared_tasks(OrganizationUser)
