from html import escape

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal
from models import User
from security import verify_password

from bot.keyboards import (
    auth_menu,
    main_menu,
)
from bot.states import LoginState


router = Router()

# старт

@router.message(CommandStart())
async def start_handler(message: Message):
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        username = (
            user.username
            if user is not None
            else None
        )

    if username:
        await message.answer(
            f"👋 С возвращением, {escape(username)}!\n\n"
            "Выберите действие 👇",
            reply_markup=main_menu(),
        )

    else:
        await message.answer(
            "👋 Добро пожаловать в StudyFlow!\n\n"
            "Чтобы получить доступ к своим задачам, "
            "сначала войдите в аккаунт StudyFlow.",
            reply_markup=auth_menu(),
        )
# ВХОД

@router.message(F.text == "🔐 Войти в StudyFlow")
async def login_start(
    message: Message,
    state: FSMContext,
):
    await state.clear()

    await state.set_state(
        LoginState.username
    )

    await message.answer(
        "🔐 <b>Вход в StudyFlow</b>\n\n"
        "Введите имя пользователя:",
        parse_mode="HTML",
    )


@router.message(LoginState.username)
async def login_username(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите имя пользователя текстом."
        )
        return

    username = message.text.strip()

    if not username:
        await message.answer(
            "❌ Имя пользователя не может быть пустым."
        )
        return

    await state.update_data(
        username=username
    )

    await state.set_state(
        LoginState.password
    )

    await message.answer(
        "🔑 Теперь введите пароль:"
    )


@router.message(LoginState.password)
async def login_password(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите пароль текстом."
        )
        return

    data = await state.get_data()

    username = data["username"]
    password = message.text

    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.username == username
            )
        )

        if (
            user is None
            or not verify_password(
                password,
                user.password_hash,
            )
        ):
            await state.clear()

            await message.answer(
                "❌ Неверное имя пользователя "
                "или пароль.",
                reply_markup=auth_menu(),
            )
            return

        if (
            user.telegram_id is not None
            and user.telegram_id != telegram_id
        ):
            await state.clear()

            await message.answer(
                "❌ Этот аккаунт StudyFlow уже "
                "привязан к другому Telegram.",
                reply_markup=auth_menu(),
            )
            return

        user.telegram_id = telegram_id

        db.commit()

    await state.clear()

    await message.answer(
        "✅ <b>Аккаунт успешно подключён!</b>\n\n"
        "Теперь вы можете управлять своими "
        "задачами через Telegram.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )