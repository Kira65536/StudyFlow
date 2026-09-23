from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user

from models import (
    Task,
    User,
)

from schemas import (
    AITaskGenerateRequest,
    AITaskGenerateResponse,
    AISaveTasksRequest,
    AISaveTasksResponse,
)

from services.ai_service import (
    generate_tasks_with_ai,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
)


# =========================================================
# ГЕНЕРАЦИЯ ЗАДАЧ
# =========================================================

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


# =========================================================
# СОХРАНЕНИЕ AI-ЗАДАЧ
# =========================================================

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