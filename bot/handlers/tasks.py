from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from database import SessionLocal
from models import Task, User

from bot.keyboards import (
    auth_menu,
    cancel_menu,
    deadline_menu,
    delete_confirm_menu,
    description_menu,
    edit_task_menu,
    main_menu,
    priority_menu,
    task_actions_menu,
)

from bot.states import (
    AddTaskState,
    EditTaskState,
)


router = Router()
#МОИ ЗАДАЧИ

@router.message(F.text == "📋 Мои задачи")
async def my_tasks_handler(message: Message):
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await message.answer(
                "🔐 Сначала войдите в аккаунт StudyFlow.",
                reply_markup=auth_menu(),
            )
            return

        tasks = db.scalars(
            select(Task)
            .where(
                Task.user_id == user.id
            )
            .order_by(
                Task.deadline.asc()
            )
        ).all()

        if not tasks:
            await message.answer(
                "📭 У вас пока нет задач.\n\n"
                "Нажмите «➕ Добавить задачу», "
                "чтобы создать первую."
            )
            return

        priority_icons = {
            "low": "🟢",
            "medium": "🟡",
            "high": "🔴",
        }

        status_names = {
            "todo": "📝 Нужно сделать",
            "in_progress": "⏳ В процессе",
            "done": "✅ Выполнено",
        }

        task_data = []

        for task in tasks:
            priority_icon = priority_icons.get(
                task.priority,
                "⚪",
            )

            status = status_names.get(
                task.status,
                task.status,
            )

            if task.deadline:
                deadline = task.deadline.strftime(
                    "%d.%m.%Y %H:%M"
                )
            else:
                deadline = "Без дедлайна"

            task_data.append(
                {
                    "id": task.id,
                    "is_done": task.status == "done",
                    "text": (
                        f"{priority_icon} "
                        f"<b>{escape(task.title)}</b>\n"
                        f"Статус: {status}\n"
                        f"Срок: {deadline}"
                    ),
                }
            )

    await message.answer(
        "📋 <b>Мои задачи</b>",
        parse_mode="HTML",
    )

    for task in task_data:
        await message.answer(
            task["text"],
            parse_mode="HTML",
            reply_markup=task_actions_menu(
                task["id"],
                task["is_done"],
            ),
        )

# ВЫПОЛНИТЬ ЗАДАЧУ

@router.callback_query(
    F.data.startswith("task_complete:")
)
async def complete_task(
    callback: CallbackQuery,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    telegram_id = callback.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await callback.answer(
                "Сначала войдите в StudyFlow.",
                show_alert=True,
            )
            return

        task = db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )

        if task is None:
            await callback.answer(
                "Задача не найдена.",
                show_alert=True,
            )
            return

        if task.status == "done":
            await callback.answer(
                "Эта задача уже выполнена.",
                show_alert=True,
            )
            return

        task.status = "done"
        task.completed = True

        task_title = task.title

        db.commit()

    await callback.answer(
        "✅ Задача выполнена!"
    )

    await callback.message.edit_text(
        "✅ <b>Задача выполнена!</b>\n\n"
        f"📌 {escape(task_title)}",
        parse_mode="HTML",
        reply_markup=task_actions_menu(
            task_id,
            is_done=True,
        ),
    )
# УДАЛЕНИЕ

@router.callback_query(
    F.data.startswith("task_delete:")
)
async def delete_task_request(
    callback: CallbackQuery,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    telegram_id = callback.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await callback.answer(
                "Сначала войдите в StudyFlow.",
                show_alert=True,
            )
            return

        task = db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )

        if task is None:
            await callback.answer(
                "Задача не найдена.",
                show_alert=True,
            )
            return

        task_title = task.title

    await callback.answer()

    await callback.message.answer(
        "⚠️ <b>Удалить задачу?</b>\n\n"
        f"📌 {escape(task_title)}\n\n"
        "После удаления восстановить её "
        "будет нельзя.",
        parse_mode="HTML",
        reply_markup=delete_confirm_menu(
            task_id
        ),
    )


@router.callback_query(
    F.data.startswith("task_delete_confirm:")
)
async def delete_task_confirm(
    callback: CallbackQuery,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    telegram_id = callback.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await callback.answer(
                "Пользователь не найден.",
                show_alert=True,
            )
            return

        task = db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )

        if task is None:
            await callback.answer(
                "Задача уже удалена или не найдена.",
                show_alert=True,
            )
            return

        task_title = task.title

        db.delete(task)
        db.commit()

    await callback.answer(
        "Задача удалена"
    )

    await callback.message.edit_text(
        "🗑 <b>Задача удалена</b>\n\n"
        f"📌 {escape(task_title)}",
        parse_mode="HTML",
    )


@router.callback_query(
    F.data.startswith("task_delete_cancel:")
)
async def delete_task_cancel(
    callback: CallbackQuery,
):
    await callback.answer()

    await callback.message.edit_text(
        "❎ Удаление отменено."
    )
# РЕДАКТИРОВАНИЕ

@router.callback_query(
    F.data.startswith("task_edit:")
)
async def edit_task_start(
    callback: CallbackQuery,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    telegram_id = callback.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await callback.answer(
                "Сначала войдите в StudyFlow.",
                show_alert=True,
            )
            return

        task = db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user.id,
            )
        )

        if task is None:
            await callback.answer(
                "Задача не найдена.",
                show_alert=True,
            )
            return

    await callback.answer()

    await callback.message.answer(
        "✏️ <b>Что изменить?</b>",
        parse_mode="HTML",
        reply_markup=edit_task_menu(
            task_id
        ),
    )
# ИЗМЕНИТЬ НАЗВАНИЕ

@router.callback_query(
    F.data.startswith("task_edit_title:")
)
async def edit_task_title_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        edit_task_id=task_id
    )

    await state.set_state(
        EditTaskState.title
    )

    await callback.answer()

    await callback.message.answer(
        "📝 Введите новое название задачи:",
        reply_markup=cancel_menu(),
    )


@router.message(EditTaskState.title)
async def edit_task_title_save(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите название текстом."
        )
        return

    title = message.text.strip()

    if not title:
        await message.answer(
            "❌ Название не может быть пустым."
        )
        return

    data = await state.get_data()

    task_id = data["edit_task_id"]
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        task = None

        if user:
            task = db.scalar(
                select(Task).where(
                    Task.id == task_id,
                    Task.user_id == user.id,
                )
            )

        if task is None:
            await state.clear()

            await message.answer(
                "❌ Задача не найдена.",
                reply_markup=main_menu(),
            )
            return

        task.title = title

        db.commit()

    await state.clear()

    await message.answer(
        "✅ Название задачи изменено!",
        reply_markup=main_menu(),
    )
# ИЗМЕНИТЬ ОПИСАНИЕ

@router.callback_query(
    F.data.startswith("task_edit_description:")
)
async def edit_task_description_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        edit_task_id=task_id
    )

    await state.set_state(
        EditTaskState.description
    )

    await callback.answer()

    await callback.message.answer(
        "📄 Введите новое описание.\n\n"
        "Или нажмите «⏭ Без описания».",
        reply_markup=description_menu(),
    )


@router.message(EditTaskState.description)
async def edit_task_description_save(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите описание текстом "
            "или нажмите «⏭ Без описания»."
        )
        return

    if message.text == "⏭ Без описания":
        description = ""
    else:
        description = message.text.strip()

    data = await state.get_data()

    task_id = data["edit_task_id"]
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        task = None

        if user:
            task = db.scalar(
                select(Task).where(
                    Task.id == task_id,
                    Task.user_id == user.id,
                )
            )

        if task is None:
            await state.clear()

            await message.answer(
                "❌ Задача не найдена.",
                reply_markup=main_menu(),
            )
            return

        task.description = description

        db.commit()

    await state.clear()

    await message.answer(
        "✅ Описание задачи изменено!",
        reply_markup=main_menu(),
    )
# ИЗМЕНИТЬ ПРИОРИТЕТ

@router.callback_query(
    F.data.startswith("task_edit_priority:")
)
async def edit_task_priority_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        edit_task_id=task_id
    )

    await state.set_state(
        EditTaskState.priority
    )

    await callback.answer()

    await callback.message.answer(
        "🎯 Выберите новый приоритет:",
        reply_markup=priority_menu(),
    )


@router.message(EditTaskState.priority)
async def edit_task_priority_save(
    message: Message,
    state: FSMContext,
):
    priorities = {
        "🟢 Низкий": "low",
        "🟡 Средний": "medium",
        "🔴 Высокий": "high",
    }

    priority = priorities.get(
        message.text
    )

    if priority is None:
        await message.answer(
            "❌ Выберите приоритет кнопкой.",
            reply_markup=priority_menu(),
        )
        return

    data = await state.get_data()

    task_id = data["edit_task_id"]
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        task = None

        if user:
            task = db.scalar(
                select(Task).where(
                    Task.id == task_id,
                    Task.user_id == user.id,
                )
            )

        if task is None:
            await state.clear()

            await message.answer(
                "❌ Задача не найдена.",
                reply_markup=main_menu(),
            )
            return

        task.priority = priority

        db.commit()

    await state.clear()

    await message.answer(
        "✅ Приоритет задачи изменён!",
        reply_markup=main_menu(),
    )
# ИЗМЕНИТЬ ДЕДЛАЙН
@router.callback_query(
    F.data.startswith("task_edit_deadline:")
)
async def edit_task_deadline_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    task_id = int(
        callback.data.split(":")[1]
    )

    await state.clear()

    await state.update_data(
        edit_task_id=task_id
    )

    await state.set_state(
        EditTaskState.deadline
    )

    await callback.answer()

    await callback.message.answer(
        "📅 Введите новый дедлайн:\n\n"
        "<b>30.09.2026 18:00</b>\n\n"
        "Или нажмите «⏭ Без дедлайна».",
        parse_mode="HTML",
        reply_markup=deadline_menu(),
    )


@router.message(EditTaskState.deadline)
async def edit_task_deadline_save(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите дедлайн текстом "
            "или нажмите «⏭ Без дедлайна»."
        )
        return

    if message.text == "⏭ Без дедлайна":
        deadline = None

    else:
        try:
            deadline = datetime.strptime(
                message.text.strip(),
                "%d.%m.%Y %H:%M",
            )

        except ValueError:
            await message.answer(
                "❌ Неверный формат даты.\n\n"
                "Например:\n"
                "<b>30.09.2026 18:00</b>",
                parse_mode="HTML",
                reply_markup=deadline_menu(),
            )
            return

    data = await state.get_data()

    task_id = data["edit_task_id"]
    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        task = None

        if user:
            task = db.scalar(
                select(Task).where(
                    Task.id == task_id,
                    Task.user_id == user.id,
                )
            )

        if task is None:
            await state.clear()

            await message.answer(
                "❌ Задача не найдена.",
                reply_markup=main_menu(),
            )
            return

        task.deadline = deadline

        db.commit()

    await state.clear()

    await message.answer(
        "✅ Дедлайн задачи изменён!",
        reply_markup=main_menu(),
    )


@router.callback_query(
    F.data.startswith("task_edit_cancel:")
)
async def edit_task_cancel(
    callback: CallbackQuery,
):
    await callback.answer()

    await callback.message.edit_text(
        "❎ Редактирование закрыто."
    )

# ДОБАВИТЬ ЗАДАЧУ

@router.message(F.text == "➕ Добавить задачу")
async def add_task_handler(
    message: Message,
    state: FSMContext,
):
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

    await state.clear()

    await state.set_state(
        AddTaskState.title
    )

    await message.answer(
        "➕ <b>Новая задача</b>\n\n"
        "Введите название задачи:",
        parse_mode="HTML",
        reply_markup=cancel_menu(),
    )


@router.message(AddTaskState.title)
async def add_task_title(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите название текстом."
        )
        return

    title = message.text.strip()

    if not title:
        await message.answer(
            "❌ Название не может быть пустым."
        )
        return

    await state.update_data(
        title=title
    )

    await state.set_state(
        AddTaskState.description
    )

    await message.answer(
        "📝 Введите описание задачи.\n\n"
        "Или нажмите «⏭ Без описания».",
        reply_markup=description_menu(),
    )


@router.message(AddTaskState.description)
async def add_task_description(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите описание текстом "
            "или нажмите «⏭ Без описания»."
        )
        return

    if message.text == "⏭ Без описания":
        description = ""
    else:
        description = message.text.strip()

    await state.update_data(
        description=description
    )

    await state.set_state(
        AddTaskState.priority
    )

    await message.answer(
        "🎯 Выберите приоритет:",
        reply_markup=priority_menu(),
    )


@router.message(AddTaskState.priority)
async def add_task_priority(
    message: Message,
    state: FSMContext,
):
    priorities = {
        "🟢 Низкий": "low",
        "🟡 Средний": "medium",
        "🔴 Высокий": "high",
    }

    priority = priorities.get(
        message.text
    )

    if priority is None:
        await message.answer(
            "❌ Выберите приоритет "
            "с помощью кнопок.",
            reply_markup=priority_menu(),
        )
        return

    await state.update_data(
        priority=priority
    )

    await state.set_state(
        AddTaskState.deadline
    )

    await message.answer(
        "📅 Введите дедлайн в формате:\n\n"
        "<b>30.09.2026 18:00</b>\n\n"
        "Или выберите «⏭ Без дедлайна».",
        parse_mode="HTML",
        reply_markup=deadline_menu(),
    )


@router.message(AddTaskState.deadline)
async def add_task_deadline(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Введите дату текстом "
            "или нажмите «⏭ Без дедлайна».",
            reply_markup=deadline_menu(),
        )
        return

    if message.text == "⏭ Без дедлайна":
        deadline = None

    else:
        try:
            deadline = datetime.strptime(
                message.text.strip(),
                "%d.%m.%Y %H:%M",
            )

        except ValueError:
            await message.answer(
                "❌ Неверный формат даты.\n\n"
                "Введите, например:\n"
                "<b>30.09.2026 18:00</b>",
                parse_mode="HTML",
                reply_markup=deadline_menu(),
            )
            return

    data = await state.get_data()

    telegram_id = message.from_user.id

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user is None:
            await state.clear()

            await message.answer(
                "❌ Пользователь не найден.",
                reply_markup=auth_menu(),
            )
            return

        task = Task(
            user_id=user.id,
            title=data["title"],
            description=data["description"],
            priority=data["priority"],
            status="todo",
            completed=False,
            deadline=deadline,
        )

        db.add(task)
        db.commit()

    await state.clear()

    if deadline:
        deadline_text = deadline.strftime(
            "%d.%m.%Y %H:%M"
        )
    else:
        deadline_text = "Без дедлайна"

    await message.answer(
        "✅ <b>Задача создана!</b>\n\n"
        f"📌 {escape(data['title'])}\n"
        f"📅 {deadline_text}",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
# ВЫПОЛНЕННЫЕ

@router.message(F.text == "✅ Выполненные")
async def completed_handler(message: Message):
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

        tasks = db.scalars(
            select(Task)
            .where(
                Task.user_id == user.id,
                Task.status == "done",
            )
            .order_by(
                Task.updated_at.desc()
            )
        ).all()

        if not tasks:
            await message.answer(
                "📭 Выполненных задач пока нет."
            )
            return

        text = (
            "✅ <b>Выполненные задачи</b>\n\n"
        )

        for task in tasks:
            text += (
                f"✅ <b>{escape(task.title)}</b>\n"
            )

            if task.description:
                text += (
                    f"📝 "
                    f"{escape(task.description)}\n"
                )

            text += "\n"

    await message.answer(
        text,
        parse_mode="HTML",
    )