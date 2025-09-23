from fastapi import APIRouter, Depends

from app.api.deps import (
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings, celery_config

from celery import Celery, signature, chain

from stack_datamodel import Message
from stack_datamodel.tasks import (
    BinaryOperandsPayloadSchema,
    BinaryOperationResultSchema,
    SampleBaseRandomVariablePayloadSchema,
    SampleResultSchema,
    BinaryIntegerOperandsPayloadSchema
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
task_queue = Celery(
    settings.PROJECT_NAME,
    broker=str(settings.RABBITMQ_URI),
    backend=str(settings.CELERY_BACKEND_DB_URI),
)
task_queue.config_from_object(celery_config)


@router.post(
    "/add",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message
)
def submit_task_add(session: SessionDep, payload: BinaryOperandsPayloadSchema) -> Message:
    task_queue.send_task('add', args=(payload.a, payload.b))
    return Message(message="Task add submitted successfully")


@router.post(
    "/add-wait",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=BinaryOperationResultSchema
)
def submit_task_add_wait(session: SessionDep, payload: BinaryOperandsPayloadSchema) -> BinaryOperationResultSchema:
    task_name = 'add'
    task = task_queue.send_task(task_name, args=(payload.a, payload.b))
    result = BinaryOperationResultSchema(s=task.wait(timeout=None, interval=0.5))
    return result


@router.post(
    "/multiply-wait",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=BinaryOperationResultSchema
)
def submit_task_multiply_wait(session: SessionDep, payload: BinaryOperandsPayloadSchema) -> BinaryOperationResultSchema:
    task_name = 'multiply'
    task = task_queue.send_task(task_name, kwargs=payload.model_dump())
    result = task.wait(timeout=None, interval=0.5)
    return result


@router.post(
    "/multiply-by-summation-wait",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=BinaryOperationResultSchema
)
def submit_task_multiply_by_summation_wait(
        session: SessionDep,
        payload: BinaryIntegerOperandsPayloadSchema
) -> BinaryOperationResultSchema:
    if payload.b == 0:
        return BinaryOperationResultSchema(s=0)
    if payload.b == 1:
        return BinaryOperationResultSchema(s=payload.a)
    job = chain(
        *(
                [task_queue.signature('add', args=(payload.a, payload.a))] +
                [
                    task_queue.signature('add', args=(payload.a,))
                    for _ in range(payload.b - 2)
                ]
        )
    )
    result = job.apply_async()
    result = BinaryOperationResultSchema(
        s=result.get()
    )
    return result


@router.post(
    "/sample-normal-wait",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SampleResultSchema
)
def submit_task_sample_normal_wait(
        session: SessionDep,
        payload: SampleBaseRandomVariablePayloadSchema
) -> SampleResultSchema:
    task_name = 'sample-normal'
    task = task_queue.send_task(task_name, kwargs=payload.model_dump())
    result = task.wait(timeout=None, interval=0.5)
    return result
