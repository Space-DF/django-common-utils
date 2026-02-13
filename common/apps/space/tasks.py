from common.apps.space.models import Space
from common.celery.tasks import create_tenant_model_shared_tasks

update_space, delete_space = create_tenant_model_shared_tasks(Space)
