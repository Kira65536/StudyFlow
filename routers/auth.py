from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import User

from schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

from security import (
    create_access_token,
    hash_password,
    verify_password,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=["Auth"]
)


# =========================================================
# РЕГИСТРАЦИЯ
# =========================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
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

    # Создаём пользователя
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
            detail="Пользователь уже существует",
        )

    db.refresh(new_user)

    return new_user


# =========================================================
# ВХОД
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):

    # Ищем пользователя по email
    user = db.scalar(
        select(User).where(
            User.email == user_data.email
        )
    )

    # Если пользователя нет
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
        )

    # Проверяем пароль
    password_correct = verify_password(
        user_data.password,
        user.password_hash,
    )

    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
        )

    # Создаём JWT
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

@router.get(
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