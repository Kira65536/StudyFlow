import jwt

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Task, User
from security import decode_access_token


# Схема авторизации Bearer Token
bearer_scheme = HTTPBearer(
    auto_error=False
)


def authorization_error(
    detail: str,
) -> HTTPException:
    """
    Стандартная ошибка авторизации.
    """

    return HTTPException(
        status_code=401,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Получает текущего пользователя
    из JWT-токена.
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
    Получает задачу только если она
    принадлежит текущему пользователю.
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