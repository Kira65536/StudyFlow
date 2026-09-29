from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


# ТИПЫ
Priority = Literal[
    "low",
    "medium",
    "high",
]

TaskStatus = Literal[
    "todo",
    "in_progress",
    "done",
]


# ЗАДАЧИ

class TaskCreate(BaseModel):
    """Данные для создания новой задачи."""

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        default="",
        max_length=5000,
    )

    priority: Priority = "medium"
    status: TaskStatus = "todo"
    deadline: datetime | None = None


class TaskUpdate(BaseModel):
    """Полное обновление задачи через PUT."""

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str = Field(
        max_length=5000
    )

    priority: Priority
    status: TaskStatus
    deadline: datetime | None = None


class TaskPatch(BaseModel):
    """Частичное обновление задачи через PATCH."""

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    priority: Priority | None = None
    status: TaskStatus | None = None
    deadline: datetime | None = None


class TaskResponse(BaseModel):
    """Задача, которую API возвращает пользователю."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    completed: bool
    deadline: datetime | None
    created_at: datetime
    updated_at: datetime


# ПОЛЬЗОВАТЕЛИ
class UserCreate(BaseModel):
    """Данные для регистрации."""

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLogin(BaseModel):
    """Данные для входа."""

    model_config = ConfigDict(
        str_strip_whitespace=True
    )

    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


class UserResponse(BaseModel):
    """Безопасные данные пользователя."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    username: str
    email: EmailStr
    created_at: datetime


# JWT
class TokenResponse(BaseModel):
    """Ответ после успешного входа."""

    access_token: str
    token_type: str


# ПРОЧИЕ ОТВЕТЫ

class TaskDeleteResponse(BaseModel):
    message: str
    task_id: int

# AI — ПЕРЕПЛАНИРОВАНИЕ

class AIReplanRequest(BaseModel):
    """Запрос на перепланирование задач."""

    days: int = Field(
        ge=1,
        le=365,
    )

    instruction: str | None = Field(
        default=None,
        max_length=1000,
    )


class AIReplannedTask(BaseModel):
    """Одна перепланированная задача."""

    task_id: int
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    deadline: datetime


class AIReplanResponse(BaseModel):
    """Ответ с новым планом."""

    days: int
    tasks: list[AIReplannedTask]

# AI — ПРИМЕНЕНИЕ ПЕРЕПЛАНИРОВАНИЯ

class AIReplanApplyTask(BaseModel):
    """Изменения одной задачи после перепланирования."""

    task_id: int
    priority: Priority
    deadline: datetime


class AIApplyReplanRequest(BaseModel):
    """План, который пользователь хочет применить."""

    tasks: list[AIReplanApplyTask] = Field(
        min_length=1,
        max_length=100,
    )


class AIApplyReplanResponse(BaseModel):
    """Результат применения нового плана."""

    updated_count: int
    tasks: list[TaskResponse]
    
# AI

class AITaskGenerateRequest(BaseModel):
    """Запрос на генерацию плана."""

    goal: str = Field(
        min_length=3,
        max_length=2000,
    )

    number_of_tasks: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    days: int | None = Field(
        default=None,
        ge=1,
        le=365,
    )


class AIGeneratedTask(BaseModel):
    """Одна задача, созданная AI."""

    title: str
    description: str = ""
    priority: Priority = "medium"
    deadline: datetime | None = None


class AITaskGenerateResponse(BaseModel):
    """Готовый AI-план."""

    goal: str
    tasks: list[AIGeneratedTask]


class AISaveTasksRequest(BaseModel):
    """Задачи, выбранные пользователем для сохранения."""

    tasks: list[AIGeneratedTask] = Field(
        min_length=1,
        max_length=20,
    )


class AISaveTasksResponse(BaseModel):
    """Результат сохранения AI-задач."""

    saved_count: int
    tasks: list[TaskResponse]


