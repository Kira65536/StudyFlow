import json

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import ollama

from schemas import (
    AITaskGenerateResponse,
    AIReplannedTask,
    AIReplanResponse,
)


# =========================================================
# НАСТРОЙКИ AI
# =========================================================

MODEL_NAME = "qwen2.5:3b"


# =========================================================
# ДЕДЛАЙНЫ ДЛЯ НОВЫХ AI-ЗАДАЧ
# =========================================================

def add_deadlines(
    result: AITaskGenerateResponse,
    days: int | None,
) -> AITaskGenerateResponse:
    """
    Равномерно распределяет дедлайны
    между сгенерированными задачами.
    """

    if days is None:
        return result

    number_of_tasks = len(
        result.tasks
    )

    if number_of_tasks == 0:
        return result

    now = datetime.now(
        timezone.utc
    )

    for index, task in enumerate(
        result.tasks,
        start=1,
    ):

        task_day = max(
            1,
            round(
                days
                * index
                / number_of_tasks
            ),
        )

        task.deadline = (
            now
            + timedelta(
                days=task_day
            )
        )

    return result


# =========================================================
# ГЕНЕРАЦИЯ НОВЫХ ЗАДАЧ
# =========================================================

def generate_tasks_with_ai(
    goal: str,
    number_of_tasks: int,
    days: int | None = None,
) -> AITaskGenerateResponse:
    """
    Генерирует новый план задач через Ollama.
    """

    period_text = ""

    if days is not None:
        period_text = (
            f"Пользователь хочет достичь цели "
            f"примерно за {days} дней."
        )

    prompt = f"""
Цель пользователя:

{goal}

{period_text}

Создай ровно {number_of_tasks} конкретных задач,
которые помогут пользователю достичь этой цели.

Расположи задачи в логическом порядке:
от первого шага до завершающего.

Задачи должны быть практичными и конкретными.

Плохо:
"Познакомиться с Python"

Хорошо:
"Повторить функции и классы Python"
"Решить 5 задач по SQL"
"Создать CRUD endpoint в FastAPI"

Для каждой задачи укажи:

- title — короткое название;
- description — конкретное действие;
- priority — только low, medium или high.

Верни ТОЛЬКО JSON.

Не используй Markdown.
Не добавляй объяснений.
Не добавляй текст перед JSON.
Не добавляй текст после JSON.

Формат:

{{
    "goal": "{goal}",
    "tasks": [
        {{
            "title": "Название задачи",
            "description": "Описание задачи",
            "priority": "medium"
        }}
    ]
}}
"""

    try:
        response = ollama.chat(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты AI-помощник приложения StudyFlow. "
                        "Всегда отвечай только на русском языке. "
                        "Создавай конкретные практические задачи. "
                        "Не используй китайский язык. "
                        "Возвращай только корректный JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            format="json",

            options={
                "temperature": 0.2,
            },
        )

    except Exception as error:
        raise RuntimeError(
            f"Не удалось подключиться к Ollama: {error}"
        )

    try:
        content = response[
            "message"
        ][
            "content"
        ]

    except Exception:
        raise RuntimeError(
            "Ollama вернул неожиданный ответ"
        )

    try:
        data = json.loads(
            content
        )

    except json.JSONDecodeError:
        raise RuntimeError(
            "AI вернул некорректный JSON"
        )

    try:
        result = (
            AITaskGenerateResponse
            .model_validate(
                data
            )
        )

    except Exception as error:
        raise RuntimeError(
            "AI вернул данные "
            f"неверного формата: {error}"
        )

    if (
        len(result.tasks)
        != number_of_tasks
    ):
        raise RuntimeError(
            "AI вернул неправильное "
            "количество задач"
        )

    result = add_deadlines(
        result=result,
        days=days,
    )

    return result


# =========================================================
# AI-ПЕРЕПЛАНИРОВАНИЕ
# =========================================================

def replan_tasks_with_ai(
    tasks: list,
    days: int,
    instruction: str | None = None,
) -> AIReplanResponse:
    """
    Перестраивает существующий план.

    AI:
    - меняет порядок задач;
    - определяет приоритет.

    Python:
    - проверяет task_id;
    - назначает новые дедлайны.

    Новые задачи не создаются.
    """

    if not tasks:
        raise RuntimeError(
            "Нет задач для перепланирования"
        )

    # -----------------------------------------------------
    # Подготавливаем задачи для AI
    # -----------------------------------------------------

    task_data = []

    for task in tasks:

        task_data.append(
            {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status,
                "deadline": (
                    task.deadline.isoformat()
                    if task.deadline
                    else None
                ),
            }
        )

    # -----------------------------------------------------
    # Дополнительное пожелание пользователя
    # -----------------------------------------------------

    instruction_text = ""

    if instruction:

        instruction_text = f"""
Дополнительное пожелание пользователя:

{instruction}
"""

    # -----------------------------------------------------
    # PROMPT
    # -----------------------------------------------------

    prompt = f"""
У пользователя есть незавершённые задачи:

{json.dumps(
    task_data,
    ensure_ascii=False,
    indent=2,
)}

Нужно перестроить план на {days} дней.

{instruction_text}

Твоя задача:

1. Расположи задачи в логическом порядке.
2. Самые важные задачи поставь раньше.
3. Измени priority при необходимости.
4. priority может быть только:
   low, medium или high.
5. НЕ создавай новые задачи.
6. НЕ удаляй задачи.
7. НЕ изменяй task_id.
8. Каждый task_id должен встретиться ровно один раз.
9. Верни все переданные задачи.

Верни ТОЛЬКО JSON.

Формат:

{{
    "tasks": [
        {{
            "task_id": 1,
            "priority": "high"
        }}
    ]
}}
"""

    # -----------------------------------------------------
    # ЗАПРОС К OLLAMA
    # -----------------------------------------------------

    try:
        response = ollama.chat(
            model=MODEL_NAME,

            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты AI-планировщик "
                        "приложения StudyFlow. "
                        "Всегда отвечай только "
                        "на русском языке. "
                        "Нельзя добавлять или "
                        "удалять задачи. "
                        "Возвращай только JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            format="json",

            options={
                "temperature": 0.2,
            },
        )

    except Exception as error:
        raise RuntimeError(
            f"Не удалось подключиться к Ollama: {error}"
        )

    # -----------------------------------------------------
    # ЧИТАЕМ ОТВЕТ
    # -----------------------------------------------------

    try:
        content = response[
            "message"
        ][
            "content"
        ]

    except Exception:
        raise RuntimeError(
            "Ollama вернул неожиданный ответ"
        )

    try:
        data = json.loads(
            content
        )

    except json.JSONDecodeError:
        raise RuntimeError(
            "AI вернул некорректный JSON"
        )

    ai_tasks = data.get(
        "tasks"
    )

    if not isinstance(
        ai_tasks,
        list,
    ):
        raise RuntimeError(
            "AI вернул неправильный "
            "формат плана"
        )

    # -----------------------------------------------------
    # ПРОВЕРКА ЗАДАЧ
    # -----------------------------------------------------

    original_tasks = {
        task.id: task
        for task in tasks
    }

    original_ids = set(
        original_tasks.keys()
    )

    received_ids = []

    allowed_priorities = {
        "low",
        "medium",
        "high",
    }

    for item in ai_tasks:

        if not isinstance(
            item,
            dict,
        ):
            raise RuntimeError(
                "AI вернул неправильный "
                "формат задачи"
            )

        task_id = item.get(
            "task_id"
        )

        priority = item.get(
            "priority"
        )

        if task_id not in original_ids:
            raise RuntimeError(
                "AI вернул неизвестную задачу"
            )

        if priority not in allowed_priorities:
            raise RuntimeError(
                "AI вернул неверный приоритет"
            )

        if task_id in received_ids:
            raise RuntimeError(
                "AI продублировал задачу"
            )

        received_ids.append(
            task_id
        )

    if set(received_ids) != original_ids:
        raise RuntimeError(
            "AI вернул не все задачи"
        )

    # -----------------------------------------------------
    # СОЗДАЁМ НОВЫЕ ДЕДЛАЙНЫ
    # -----------------------------------------------------

    now = datetime.now(
        timezone.utc
    )

    number_of_tasks = len(
        ai_tasks
    )

    result_tasks = []

    for index, item in enumerate(
        ai_tasks,
        start=1,
    ):

        task_id = item[
            "task_id"
        ]

        original_task = original_tasks[
            task_id
        ]

        task_day = max(
            1,
            round(
                days
                * index
                / number_of_tasks
            ),
        )

        deadline = (
            now
            + timedelta(
                days=task_day
            )
        )

        replanned_task = AIReplannedTask(
            task_id=original_task.id,
            title=original_task.title,
            description=original_task.description,
            priority=item["priority"],
            status=original_task.status,
            deadline=deadline,
        )

        result_tasks.append(
            replanned_task
        )

    # -----------------------------------------------------
    # ГОТОВЫЙ ПЛАН
    # -----------------------------------------------------

    return AIReplanResponse(
        days=days,
        tasks=result_tasks,
    )