from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from sqlalchemy import (
    select,
    or_,
)

from sqlalchemy.orm import Session

from database import get_db
from dependencies import (
    get_current_user,
    get_user_task,
)

from models import (
    Task,
    User,
)

from schemas import (
    Priority,
    TaskStatus,
    TaskCreate,
    TaskUpdate,
    TaskPatch,
    TaskResponse,
    TaskDeleteResponse,
)


#ROUTER

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


#ПОЛУЧИТЬ ВСЕ ЗАДАЧИ

@router.get(
    "",
    response_model=list[TaskResponse],
)
def get_tasks(

    status: TaskStatus | None = None,

    priority: Priority | None = None,

    search: str | None = Query(
        default=None,
        max_length=200,
    ),

    sort_by: Literal[
        "created_at",
        "updated_at",
        "deadline",
        "title",
    ] = "created_at",

    order: Literal[
        "asc",
        "desc",
    ] = "desc",

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    statement = select(Task).where(
        Task.user_id == current_user.id
    )

    # Фильтр по статусу
    if status is not None:
        statement = statement.where(
            Task.status == status
        )

    # Фильтр по приоритету
    if priority is not None:
        statement = statement.where(
            Task.priority == priority
        )

    # Поиск по title и description
    if search:

        search = search.strip()

        if search:
            statement = statement.where(
                or_(
                    Task.title.ilike(
                        f"%{search}%"
                    ),
                    Task.description.ilike(
                        f"%{search}%"
                    ),
                )
            )

    # Доступные колонки сортировки
    sort_columns = {
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
        "deadline": Task.deadline,
        "title": Task.title,
    }

    sort_column = sort_columns[
        sort_by
    ]

    # Направление сортировки
    if order == "asc":

        statement = statement.order_by(
            sort_column
            .asc()
            .nulls_last()
        )

    else:

        statement = statement.order_by(
            sort_column
            .desc()
            .nulls_last()
        )

    # Пагинация
    statement = (
        statement
        .offset(offset)
        .limit(limit)
    )

    tasks = db.scalars(
        statement
    ).all()

    return tasks


#ПОЛУЧИТЬ ОДНУ ЗАДАЧУ.

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    return get_user_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

# СОЗДАТЬ ЗАДАЧУ

@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
)
def create_task(
    task_data: TaskCreate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status=task_data.status,
        deadline=task_data.deadline,

        completed=(
            task_data.status == "done"
        ),

        user_id=current_user.id,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task
# ПОЛНОЕ ОБНОВЛЕНИЕ ЗАДАЧИ

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: int,

    task_data: TaskUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = get_user_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.status = task_data.status
    task.deadline = task_data.deadline

    task.completed = (
        task_data.status == "done"
    )

    db.commit()
    db.refresh(task)

    return task


#ЧАСТИЧНОЕ ОБНОВЛЕНИЕ ЗАДАЧИ

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def patch_task(
    task_id: int,

    task_data: TaskPatch,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = get_user_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    update_data = task_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        setattr(
            task,
            field,
            value,
        )

    # completed автоматически зависит от status
    if "status" in update_data:

        task.completed = (
            task.status == "done"
        )

    db.commit()
    db.refresh(task)

    return task

#УДАЛЕНИЕ ЗАДАЧИ

@router.delete(
    "/{task_id}",
    response_model=TaskDeleteResponse,
)
def delete_task(
    task_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    task = get_user_task(
        task_id=task_id,
        user_id=current_user.id,
        db=db,
    )

    db.delete(task)
    db.commit()

    return {
        "message": "Задача удалена",
        "task_id": task_id,
    }