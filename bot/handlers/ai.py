import asyncio

from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal
from models import Task, User

from services.ai_service import (
    generate_tasks_with_ai,
    replan_tasks_with_ai,
)

from bot.keyboards import (
    ai_plan_menu,
    auth_menu,
    cancel_menu,
    main_menu,
    replan_instruction_menu,
    replan_preview_menu,
)

from bot.states import (
    AIPlanState,
    AIReplanState,
)


router = Router()

# AI-ПЛАН

@router.message(F.text == "🤖 AI-план")
async def ai_plan_start(
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
            "🔐 Сначала войдите в StudyFlow.",
            reply_markup=auth_menu(),
        )
        return

    await state.clear()

    await state.set_state(
        AIPlanState.goal
    )

    await message.answer(
        "🤖 <b>AI-план</b>\n\n"
        "🎯 Напишите вашу цель.\n\n"
        "Например:\n"
        "<i>Подготовиться к собеседованию "
        "Python backend разработчика</i>",
        parse_mode="HTML",
        reply_markup=cancel_menu(),
    )
# ЦЕЛЬ

@router.message(AIPlanState.goal)
async def ai_plan_goal(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Напишите цель текстом."
        )
        return

    goal = message.text.strip()

    if len(goal) < 3:
        await message.answer(
            "❌ Цель слишком короткая."
        )
        return

    await state.update_data(
        goal=goal
    )

    await state.set_state(
        AIPlanState.days
    )

    await message.answer(
        "📅 За сколько дней нужно "
        "достичь этой цели?\n\n"
        "Например: <b>7</b>",
        parse_mode="HTML",
        reply_markup=cancel_menu(),
    )
# КОЛИЧЕСТВО ДНЕЙ

@router.message(AIPlanState.days)
async def ai_plan_days(
    message: Message,
    state: FSMContext,
):
    try:
        days = int(
            message.text.strip()
        )

    except (ValueError, AttributeError):
        await message.answer(
            "❌ Введите количество дней числом.\n"
            "Например: 7"
        )
        return

    if days < 1 or days > 365:
        await message.answer(
            "❌ Количество дней должно быть "
            "от 1 до 365."
        )
        return

    await state.update_data(
        days=days
    )

    await state.set_state(
        AIPlanState.number_of_tasks
    )

    await message.answer(
        "📋 Сколько задач создать?\n\n"
        "Например: <b>5</b>",
        parse_mode="HTML",
        reply_markup=cancel_menu(),
    )
# КОЛИЧЕСТВО ЗАДАЧ

@router.message(AIPlanState.number_of_tasks)
async def ai_plan_number_of_tasks(
    message: Message,
    state: FSMContext,
):
    try:
        number_of_tasks = int(
            message.text.strip()
        )

    except (ValueError, AttributeError):
        await message.answer(
            "❌ Введите количество задач числом.\n"
            "Например: 5"
        )
        return

    if (
        number_of_tasks < 1
        or number_of_tasks > 15
    ):
        await message.answer(
            "❌ Можно создать от 1 до 15 задач."
        )
        return

    await state.update_data(
        number_of_tasks=number_of_tasks
    )

    await generate_ai_plan(
        message=message,
        state=state,
    )
# ГЕНЕРАЦИЯ AI-ПЛАНА
async def generate_ai_plan(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    await message.answer(
        "🤖 Генерирую план...\n"
        "Это может занять немного времени."
    )

    try:
        result = await asyncio.to_thread(
            generate_tasks_with_ai,
            data["goal"],
            data["number_of_tasks"],
            data["days"],
        )

    except RuntimeError as error:
        await state.clear()

        await message.answer(
            "❌ Не удалось создать AI-план.\n\n"
            f"{escape(str(error))}",
            reply_markup=main_menu(),
        )
        return

    generated_tasks = []

    priority_icons = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
    }

    text = (
        "🤖 <b>AI-план готов!</b>\n\n"
        f"🎯 <b>Цель:</b> "
        f"{escape(data['goal'])}\n"
        f"📅 <b>Период:</b> "
        f"{data['days']} дней\n\n"
    )

    for index, task in enumerate(
        result.tasks,
        start=1,
    ):
        generated_tasks.append(
            {
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "deadline": (
                    task.deadline.isoformat()
                    if task.deadline
                    else None
                ),
            }
        )

        icon = priority_icons.get(
            task.priority,
            "⚪",
        )

        if task.deadline:
            deadline_text = (
                task.deadline.strftime(
                    "%d.%m.%Y %H:%M"
                )
            )
        else:
            deadline_text = "Без дедлайна"

        text += (
            f"{index}. {icon} "
            f"<b>{escape(task.title)}</b>\n"
            f"📝 {escape(task.description)}\n"
            f"📅 {deadline_text}\n\n"
        )

    await state.update_data(
        generated_tasks=generated_tasks
    )

    await state.set_state(
        AIPlanState.preview
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=ai_plan_menu(),
    )
# СОХРАНИТЬ AI-ПЛАН
@router.message(
    AIPlanState.preview,
    F.text == "💾 Сохранить AI-план",
)
async def save_ai_plan(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    generated_tasks = data.get(
        "generated_tasks",
        []
    )

    if not generated_tasks:
        await state.clear()

        await message.answer(
            "❌ Сгенерированный план не найден.",
            reply_markup=main_menu(),
        )
        return

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

        for generated_task in generated_tasks:
            deadline = None

            if generated_task["deadline"]:
                deadline = datetime.fromisoformat(
                    generated_task["deadline"]
                )

            task = Task(
                user_id=user.id,
                title=generated_task["title"],
                description=generated_task[
                    "description"
                ],
                priority=generated_task[
                    "priority"
                ],
                status="todo",
                completed=False,
                deadline=deadline,
            )

            db.add(task)

        db.commit()

    saved_count = len(
        generated_tasks
    )

    await state.clear()

    await message.answer(
        "✅ <b>AI-план сохранён!</b>\n\n"
        f"📋 Создано задач: {saved_count}\n\n"
        "Теперь они находятся в разделе "
        "«📋 Мои задачи».",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# СГЕНЕРИРОВАТЬ AI-ПЛАН ЗАНОВО

@router.message(
    AIPlanState.preview,
    F.text == "🔄 Сгенерировать заново",
)
async def regenerate_ai_plan(
    message: Message,
    state: FSMContext,
):
    await generate_ai_plan(
        message=message,
        state=state,
    )


#AI-ПЕРЕПЛАНИРОВАНИЕ.
@router.message(F.text == "🔄 Перепланировать")
async def replan_start(
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
                "🔐 Сначала войдите в StudyFlow.",
                reply_markup=auth_menu(),
            )
            return

        tasks = db.scalars(
            select(Task).where(
                Task.user_id == user.id,
                Task.status != "done",
            )
        ).all()

        if not tasks:
            await message.answer(
                "📭 У вас нет незавершённых задач "
                "для перепланирования."
            )
            return

        tasks_count = len(tasks)

    await state.clear()

    await state.set_state(
        AIReplanState.days
    )

    await message.answer(
        "🔄 <b>AI-перепланирование</b>\n\n"
        f"📋 Незавершённых задач: "
        f"<b>{tasks_count}</b>\n\n"
        "📅 На сколько дней распределить задачи?\n\n"
        "Например: <b>5</b>",
        parse_mode="HTML",
        reply_markup=cancel_menu(),
    )


# ДНИ

@router.message(AIReplanState.days)
async def replan_days(
    message: Message,
    state: FSMContext,
):
    try:
        days = int(
            message.text.strip()
        )

    except (ValueError, AttributeError):
        await message.answer(
            "❌ Введите количество дней числом.\n"
            "Например: 5"
        )
        return

    if days < 1 or days > 365:
        await message.answer(
            "❌ Количество дней должно быть "
            "от 1 до 365."
        )
        return

    await state.update_data(
        days=days
    )

    await state.set_state(
        AIReplanState.instruction
    )

    await message.answer(
        "💬 Есть дополнительные пожелания?\n\n"
        "Например:\n"
        "<i>Сначала задачи по FastAPI, "
        "потом SQL</i>\n\n"
        "Или нажмите «⏭ Без пожеланий».",
        parse_mode="HTML",
        reply_markup=replan_instruction_menu(),
    )


# ПОЖЕЛАНИЕ
@router.message(AIReplanState.instruction)
async def replan_instruction(
    message: Message,
    state: FSMContext,
):
    if not message.text:
        await message.answer(
            "❌ Напишите пожелание текстом "
            "или нажмите «⏭ Без пожеланий»."
        )
        return

    if message.text == "⏭ Без пожеланий":
        instruction = None

    else:
        instruction = message.text.strip()

    await state.update_data(
        instruction=instruction
    )

    await generate_replan(
        message=message,
        state=state,
    )


#ЕНЕРАЦИЯ НОВОГО ПЛАНА

async def generate_replan(
    message: Message,
    state: FSMContext,
):
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

        tasks = db.scalars(
            select(Task).where(
                Task.user_id == user.id,
                Task.status != "done",
            )
        ).all()

        if not tasks:
            await state.clear()

            await message.answer(
                "📭 Незавершённых задач больше нет.",
                reply_markup=main_menu(),
            )
            return

        try:
            result = await asyncio.to_thread(
                replan_tasks_with_ai,
                tasks,
                data["days"],
                data.get("instruction"),
            )

        except RuntimeError as error:
            await state.clear()

            await message.answer(
                "❌ Не удалось перепланировать задачи.\n\n"
                f"{escape(str(error))}",
                reply_markup=main_menu(),
            )
            return

    priority_icons = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
    }

    replanned_tasks = []

    text = (
        "🤖 <b>Новый план готов!</b>\n\n"
        f"📅 Период: "
        f"<b>{data['days']} дней</b>\n\n"
    )

    for index, task in enumerate(
        result.tasks,
        start=1,
    ):
        replanned_tasks.append(
            {
                "task_id": task.task_id,
                "title": task.title,
                "priority": task.priority,
                "deadline": (
                    task.deadline.isoformat()
                    if task.deadline
                    else None
                ),
            }
        )

        icon = priority_icons.get(
            task.priority,
            "⚪",
        )

        if task.deadline:
            deadline_text = task.deadline.strftime(
                "%d.%m.%Y %H:%M"
            )
        else:
            deadline_text = "Без дедлайна"

        text += (
            f"{index}. {icon} "
            f"<b>{escape(task.title)}</b>\n"
            f"📅 {deadline_text}\n\n"
        )

    await state.update_data(
        replanned_tasks=replanned_tasks
    )

    await state.set_state(
        AIReplanState.preview
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=replan_preview_menu(),
    )


#ПРИМЕНИТЬ НОВЫЙ ПЛАН.

@router.message(
    AIReplanState.preview,
    F.text == "✅ Применить новый план",
)
async def apply_replan(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    replanned_tasks = data.get(
        "replanned_tasks",
        []
    )

    if not replanned_tasks:
        await state.clear()

        await message.answer(
            "❌ Новый план не найден.",
            reply_markup=main_menu(),
        )
        return

    telegram_id = message.from_user.id

    task_ids = [
        item["task_id"]
        for item in replanned_tasks
    ]

    if len(task_ids) != len(set(task_ids)):
        await state.clear()

        await message.answer(
            "❌ В новом плане обнаружены "
            "повторяющиеся задачи.",
            reply_markup=main_menu(),
        )
        return

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

        tasks = db.scalars(
            select(Task).where(
                Task.user_id == user.id,
                Task.id.in_(task_ids),
            )
        ).all()

        if len(tasks) != len(task_ids):
            await state.clear()

            await message.answer(
                "❌ Одна или несколько задач "
                "больше не существуют.",
                reply_markup=main_menu(),
            )
            return

        tasks_by_id = {
            task.id: task
            for task in tasks
        }

        for task in tasks:
            if task.status == "done":
                await state.clear()

                await message.answer(
                    "⚠️ Одна из задач уже выполнена.\n\n"
                    "Создайте новый план ещё раз.",
                    reply_markup=main_menu(),
                )
                return

        for planned_task in replanned_tasks:
            task = tasks_by_id[
                planned_task["task_id"]
            ]

            task.priority = planned_task[
                "priority"
            ]

            if planned_task["deadline"]:
                task.deadline = datetime.fromisoformat(
                    planned_task["deadline"]
                )
            else:
                task.deadline = None

        db.commit()

    updated_count = len(
        replanned_tasks
    )

    await state.clear()

    await message.answer(
        "✅ <b>Новый план применён!</b>\n\n"
        f"🔄 Обновлено задач: "
        f"<b>{updated_count}</b>\n\n"
        "Новые приоритеты и дедлайны "
        "уже сохранены.",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


#ПЕРЕСЧИТАТЬ ПЛАН

@router.message(
    AIReplanState.preview,
    F.text == "🔄 Пересчитать план",
)
async def regenerate_replan(
    message: Message,
    state: FSMContext,
):
    await generate_replan(
        message=message,
        state=state,
    )