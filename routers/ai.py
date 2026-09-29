from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from schemas import (
    AITaskGenerateRequest,
    AITaskGenerateResponse,
    AISaveTasksRequest,
    AISaveTasksResponse,
    AIReplanRequest,
    AIReplanResponse,
    AIApplyReplanRequest,
    AIApplyReplanResponse,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user

from models import (
    Task,
    User,
)

from services.ai_service import (
    generate_tasks_with_ai,
    replan_tasks_with_ai,
)

#ROUTER
router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)

#ГЕНЕРАЦИЯ ЗАДАЧ

@router.post(
    "/generate-tasks",
    response_model=AITaskGenerateResponse,
)
def generate_tasks(
    request: AITaskGenerateRequest,

    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Генерирует план задач с помощью AI.

    На этом этапе задачи ещё
    не сохраняются в PostgreSQL.
    """

    try:
        return generate_tasks_with_ai(
            goal=request.goal,
            number_of_tasks=request.number_of_tasks,
            days=request.days,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )
# СОХРАНЕНИЕ AI-ЗАДАЧ

@router.post(
    "/save-tasks",
    response_model=AISaveTasksResponse,
    status_code=201,
)
def save_ai_tasks(
    request: AISaveTasksRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Сохраняет выбранные AI-задачи
    в PostgreSQL.
    """

    created_tasks = []

    for generated_task in request.tasks:

        task = Task(
            title=generated_task.title,
            description=generated_task.description,
            priority=generated_task.priority,

            status="todo",
            completed=False,
            deadline=generated_task.deadline,
            user_id=current_user.id,
        )

        db.add(task)

        created_tasks.append(task)

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Не удалось сохранить задачи",
        )

    for task in created_tasks:
        db.refresh(task)

    return {
        "saved_count": len(created_tasks),
        "tasks": created_tasks,
    }


# AI — ПРИМЕНИТЬ НОВЫЙ ПЛАН

@router.post(
    "/apply-replan",
    response_model=AIApplyReplanResponse,
)
def apply_replan(
    request: AIApplyReplanRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):
    """
    Применяет подтверждённый AI-план
    к существующим задачам пользователя.
    """

    task_ids = [
        item.task_id
        for item in request.tasks
    ]

    # Проверяем дубли ID
    if len(task_ids) != len(set(task_ids)):
        raise HTTPException(
            status_code=400,
            detail="В плане есть повторяющиеся task_id",
        )

    # Получаем только задачи текущего пользователя
    tasks = db.scalars(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.id.in_(task_ids),
        )
    ).all()

    # Проверяем, что все задачи найдены
    if len(tasks) != len(task_ids):
        raise HTTPException(
            status_code=404,
            detail=(
                "Одна или несколько задач "
                "не найдены"
            ),
        )

    tasks_by_id = {
        task.id: task
        for task in tasks
    }

    # Если пользователь успел закончить задачу,после генерации нового плана
    for task in tasks:

        if task.status == "done":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Задача {task.id} уже завершена. "
                    "Сначала создайте новый план."
                ),
            )

    # Применяем изменения
    for planned_task in request.tasks:

        task = tasks_by_id[
            planned_task.task_id
        ]

        task.priority = (
            planned_task.priority
        )

        task.deadline = (
            planned_task.deadline
        )

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Не удалось применить "
                "новый план"
            ),
        )

    # Обновляем объекты после commit
    for task in tasks:
        db.refresh(task)

    return {
        "updated_count": len(tasks),
        "tasks": tasks,
    }

@router.post(
    "/replan",
    response_model=AIReplanResponse,
)
def replan_tasks(
    request: AIReplanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    tasks = db.scalars(
        select(Task).where(
            Task.user_id == current_user.id,
            Task.status != "done",
        )
    ).all()

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="Нет незавершённых задач для перепланирования",
        )

    try:
        return replan_tasks_with_ai(
            tasks=tasks,
            days=request.days,
            instruction=request.instruction,
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )