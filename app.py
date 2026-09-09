from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import select, or_
from typing import Literal
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
import jwt
from models import Task, User
from database import get_db
from schemas import TaskCreate, TaskUpdate, TaskPatch, TaskResponse
from schemas import (
    TaskCreate,
    TaskUpdate,
    TaskPatch,
    TaskResponse,
    UserCreate,
    UserResponse,
    UserLogin,
)

app = FastAPI(
    title="StudyFlow API",
    description="Backend для StudyFlow Bot",
    version="1.0.0",
)

bearer_scheme = HTTPBearer()
@app.get("/")
def home():
    return {
        "message": "StudyFlow API работает"
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.post(
#адрес, на который пользователь отправляет данные регистрации
    "/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    existing_username = db.scalar(
        select(User).where(
            User.username == user_data.username
        )
    )

    if existing_username is not None:
        raise HTTPException(
            status_code=409,
            detail="Имя пользователя уже занято"
        )

    existing_email = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    if existing_email is not None:
        raise HTTPException(
            status_code=409,
            detail="Email уже зарегистрирован"
        )

    hashed_password = hash_password(
        user_data.password
    )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/login")
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль"
        )

    password_is_correct = verify_password(
        user_data.password,
        user.password_hash
    )

    if not password_is_correct:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль"
        )

    access_token = create_access_token(
        user.id
    )
    return { 
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):

    token = credentials.credentials
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Недействительный или просроченный токен",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Пользователь не найден",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    return user

@app.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):

    return current_user

@app.get(
    "/tasks",
    response_model=list[TaskResponse]
)

def get_tasks(
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    sort_by: Literal[
        "created_at",
        "updated_at",
        "deadline",
        "title"
    ] = "created_at",

      order: Literal[
        "asc",
        "desc"
    ] = "desc",

    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    
    statement = select(Task)
    if status is not None:
        statement = statement.where(
            Task.status == status
        )
    if priority is not None:
        statement = statement.where(
            Task.priority == priority
        )
    if search is not None:
        statement = statement.where(
            or_(
                Task.title.ilike(
                    f"%{search}%"
                ),
                Task.description.ilike(
                    f"%{search}%"
                )
            )
        )

    sort_columns = {
        "created_at": Task.created_at,
        "updated_at": Task.updated_at,
        "deadline": Task.deadline,
        "title": Task.title,
    }
    sort_column = sort_columns[sort_by]
    if order == "asc":
        statement = statement.order_by(
            sort_column.asc().nulls_last()
        )
    else:
        statement = statement.order_by(
            sort_column.desc().nulls_last()
        )
    statement = statement.offset(offset)
    statement = statement.limit(limit)
    tasks = db.scalars(statement).all()
    return tasks

@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    return task

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=201
)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):
    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        status = task_data.status,
        deadline = task_data.deadline,
        completed=task_data.status == "done",
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.put(
    "/tasks/{task_id}",
    response_model=TaskResponse
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):

    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.status = task_data.status
    task.deadline = task_data.deadline
    task.completed = task_data.status == "done"

    db.commit()
    db.refresh(task)
    return task

@app.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse
)

def patch_task(
    task_id: int,
    task_data: TaskPatch,
    db: Session = Depends(get_db)
):
    
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail= "Задача не найдена"
        )
    update_data = task_data.model_dump(
        exclude_unset= True
    )

    for field, value in update_data.items():
        setattr(
            task,
            field,
            value
        )

        if "status" in update_data:
            task.completed = task.status == 'done'

            db.commit()
            db.refresh(task)
            return task
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    task.title = task_data.title
    task.description = task_data.description
    task.priority = task_data.priority
    task.completed = task_data.status == "done"   
    task.deadline = task_data.deadline

    db.commit()
    db.refresh(task)

    return task

@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Задача не найдена"
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Задача удалена"
    }

