from celery import shared_task


@shared_task(bind=True, name='add')
def add(self, a: float, b: float) -> float:
    return a + b
