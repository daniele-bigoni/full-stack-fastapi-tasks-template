from stack_settings import Settings
from celery import Celery

settings = Settings()
app = Celery(
    settings.PROJECT_NAME,
    broker=str(settings.RABBITMQ_URI),
    backend=str(settings.CELERY_BACKEND_DB_URI),
    # include=['tasks']
)


if __name__ == '__main__':
    app.start()
