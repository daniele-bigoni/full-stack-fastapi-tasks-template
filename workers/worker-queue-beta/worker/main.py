from .core.config import settings, celery_config
from celery import Celery

from stack_datamodel.tasks import SampleBaseRandomVariablePayloadSchema, SampleResultSchema

from scipy import stats

app = Celery(
    settings.PROJECT_NAME,
    broker=str(settings.RABBITMQ_URI),
    backend=str(settings.CELERY_BACKEND_DB_URI),
)
app.config_from_object(celery_config)
app.autodiscover_tasks(
    packages=['stack_shared_tasks']
)


@app.task(bind=True, name='sample-normal')
def sample_student(self, **payload) -> SampleResultSchema:
    payload = SampleBaseRandomVariablePayloadSchema(**payload)
    d = stats.norm(loc=payload.loc, scale=payload.scale)
    return SampleResultSchema(s=d.rvs(1))


if __name__ == '__main__':
    app.start()
