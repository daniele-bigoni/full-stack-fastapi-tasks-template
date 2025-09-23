from typing import Union

from stack_settings import Settings as GeneralSettings
from stack_settings import CeleryConfig as GeneralCeleryConfig


class Settings(GeneralSettings):
    pass


settings = Settings()


class CeleryConfig(GeneralCeleryConfig):
    # The number of concurrent worker processes/threads/green threads executing tasks.
    worker_concurrency: Union[None, int] = 1

    # Messages to prefetch at a time multiplied by the number of concurrent processes
    worker_prefetch_multiplier: int = 1

    # Maximum number of tasks a pool worker process can execute before it’s replaced with a new one. None = no limit
    worker_max_tasks_per_child: Union[None, int] = None

    # Maximum amount of resident memory, in kilobytes,
    # that may be consumed by a worker before it will be replaced by a new worker.
    worker_max_memory_per_child: Union[None, int] = None

    # Name of the pool class used by the worker.
    worker_pool: str = 'prefork'


celery_config = CeleryConfig()