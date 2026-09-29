from html import escape

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal
from models import User

from bot.keyboards import (
    auth_menu,
)


router = Router()
# ПРОФИЛЬ

@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message):
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await message.answer(
                "🔐 Сначала войдите "
                "в аккаунт StudyFlow.",
                reply_markup=auth_menu(),
            )
            return

        username = user.username
        email = user.email

        total_tasks = len(
            user.tasks
        )

        completed_tasks = sum(
            1
            for task in user.tasks
            if task.status == "done"
        )

        active_tasks = (
            total_tasks
            - completed_tasks
        )

    await message.answer(
        "👤 <b>Профиль StudyFlow</b>\n\n"
        f"Имя: <b>{escape(username)}</b>\n"
        f"Email: {escape(email)}\n\n"
        f"📋 Всего задач: {total_tasks}\n"
        f"⏳ Активных: {active_tasks}\n"
        f"✅ Выполнено: {completed_tasks}",
        parse_mode="HTML",
    )