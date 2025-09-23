from .core.config import settings, celery_config
from celery import Celery, signature

from stack_datamodel.tasks import (
    BinaryOperandsPayloadSchema,
    BinaryOperationResultSchema
)

app = Celery(
    settings.PROJECT_NAME,
    broker=str(settings.RABBITMQ_URI),
    backend=str(settings.CELERY_BACKEND_DB_URI),
)
app.config_from_object(celery_config)
app.autodiscover_tasks(
    packages=['stack_shared_tasks']
)


@app.task(bind=True, name='multiply')
def multiply(self, **payload) -> BinaryOperationResultSchema:
    payload = BinaryOperandsPayloadSchema(**payload)
    return BinaryOperationResultSchema(s=payload.a * payload.b)


if __name__ == '__main__':
    app.start()
