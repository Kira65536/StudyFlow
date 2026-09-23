from typing import Literal

import jwt

from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Query,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from sqlalchemy import (
    select,
    or_,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db

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
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
)

from security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="StudyFlow API",
    description=(
        "Backend API для StudyFlow — "
        "управление пользователями и задачами."
    ),
    version="1.0.0",
)


# =========================================================
# JWT / BEARER
# =========================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def authorization_error(
    detail: str
) -> HTTPException:
    """
    Создаёт стандартную ошибку авторизации.
    """

    return HTTPException(
        status_code=401,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def get_current_user(
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(bearer_scheme),

    db: Session = Depends(get_db),

) -> User:
    """
    Получает пользователя из JWT-токена.
    """

    if credentials is None:
        raise authorization_error(
            "Необходима авторизация"
        )

    token = credentials.credentials

    try:
        user_id = decode_access_token(token)

    except jwt.ExpiredSignatureError:
        raise authorization_error(
            "Токен просрочен"
        )

    except (
        jwt.InvalidTokenError,
        ValueError,
    ):
        raise authorization_error(
            "Недействительный токен"
        )

    user = db.get(
        User,
        user_id,
    )

    if user is None:
        raise authorization_error(
            "Пользователь не найден"
        )

    return user


def get_user_task(
    task_id: int,
    user_id: int,
    db: Session,
) -> Task:
    """
    Получает задачу только в том случае,
    если она принадлежит текущему пользователю.
    """

    task = db.scalar(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена",
        )

    return task


# =========================================================
# СИСТЕМА
# =========================================================

@app.get(
    "/",
    tags=["System"],
)
def home():

    return {
        "name": "StudyFlow API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get(
    "/health",
    tags=["System"],
)
def health():

    return {
        "status": "ok"
    }


# =========================================================
# РЕГИСТРАЦИЯ
# =========================================================

@app.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    tags=["Auth"],
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):

    # Проверяем username
    existing_username = db.scalar(
        select(User).where(
            User.username == user_data.username
        )
    )

    if existing_username is not None:
        raise HTTPException(
            status_code=409,
            detail="Имя пользователя уже занято",
        )

    # Проверяем email
    existing_email = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    if existing_email is not None:
        raise HTTPException(
            status_code=409,
            detail="Email уже зарегистрирован",
        )

    # Хешируем пароль
    password_hash = hash_password(
        user_data.password
    )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
    )

    db.add(new_user)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Пользователь с такими "
                "данными уже существует"
            ),
        )

    db.refresh(new_user)

    return new_user


# =========================================================
# ВХОД
# =========================================================

@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["Auth"],
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
        )

    password_correct = verify_password(
        user_data.password,
        user.password_hash,
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
        )

    access_token = create_access_token(
        user.id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# =========================================================
# ТЕКУЩИЙ ПОЛЬЗОВАТЕЛЬ
# =========================================================

@app.get(
    "/me",
    response_model=UserResponse,
    tags=["Users"],
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return current_user


# =========================================================
# ПОЛУЧИТЬ ВСЕ ЗАДАЧИ
# =========================================================

@app.get(
    "/tasks",
    response_model=list[TaskResponse],
    tags=["Tasks"],
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

    # Пользователь получает
    # только свои задачи
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

    # Колонки для сортировки
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


# =========================================================
# ПОЛУЧИТЬ ОДНУ ЗАДАЧУ
# =========================================================

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
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


# =========================================================
# СОЗДАТЬ ЗАДАЧУ
# =========================================================

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201,
    tags=["Tasks"],
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


# =========================================================
# ПОЛНОСТЬЮ ОБНОВИТЬ ЗАДАЧУ
# =========================================================

@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
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


# =========================================================
# ЧАСТИЧНО ОБНОВИТЬ ЗАДАЧУ
# =========================================================

@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Tasks"],
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

    # Получаем только те поля,
    # которые пользователь действительно отправил
    update_data = task_data.model_dump(
        exclude_unset=True
    )

    # Эти поля нельзя устанавливать в NULL
    required_fields = {
        "title",
        "description",
        "priority",
        "status",
    }

    for field in required_fields:

        if (
            field in update_data
            and update_data[field] is None
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Поле '{field}' "
                    "не может быть null"
                ),
            )

    # Обновляем поля
    for field, value in update_data.items():

        setattr(
            task,
            field,
            value,
        )

    # completed автоматически
    # синхронизируется со status
    if "status" in update_data:

        task.completed = (
            task.status == "done"
        )

    db.commit()
    db.refresh(task)

    return task


# =========================================================
# УДАЛИТЬ ЗАДАЧУ
# =========================================================

@app.delete(
    "/tasks/{task_id}",
    response_model=TaskDeleteResponse,
    tags=["Tasks"],
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