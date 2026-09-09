from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr
#Разрешённые значения приоритета
Priority = Literal[
    "low",
    "medium",
    "high"
]
# Разрешённые статусы задачи
TaskStatus = Literal[
    "todo",
    "in_progress",
    "done"
]

#Для создания задачи     
class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: Priority = "medium"
    status: TaskStatus = "todo"
    deadline: datetime | None = None

# Данные для полного изменения задачи
class TaskUpdate(BaseModel):
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    deadline: datetime | None = None

# Данные для частивного изменения 
class TaskPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    status: TaskStatus | None = None
    deadline: datetime | None = None

#То, что FastAPI возвращает пользователю
class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: Priority
    completed: bool
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    model_config = {
        "from_attributes": True
    }

#регистрация пользователя 
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

#Данные, которые можно вернуть
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime
    model_config = {
        "from_attributes": True
    }
