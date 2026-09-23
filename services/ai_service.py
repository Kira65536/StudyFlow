import json

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import ollama

from schemas import AITaskGenerateResponse


MODEL_NAME = "qwen2.5:3b"


def add_deadlines(
    result: AITaskGenerateResponse,
    days: int | None,
) -> AITaskGenerateResponse:
    """
    Распределяет задачи по указанному количеству дней.
    """

    if days is None:
        return result

    number_of_tasks = len(result.tasks)

    if number_of_tasks == 0:
        return result

    now = datetime.now(timezone.utc)

    for index, task in enumerate(
        result.tasks,
        start=1,
    ):
        # Равномерно распределяем задачи
        # по всему указанному периоду
        task_day = max(
            1,
            round(
                days * index / number_of_tasks
            ),
        )

        task.deadline = (
            now + timedelta(days=task_day)
        )

    return result


def generate_tasks_with_ai(
    goal: str,
    number_of_tasks: int,
    days: int | None = None,
) -> AITaskGenerateResponse:
    """
    Генерирует план задач через Ollama.
    """

    period_text = ""

    if days is not None:
        period_text = (
            f"\nПользователь хочет достичь цели "
            f"примерно за {days} дней."
        )

    prompt = f"""
Цель пользователя:

{goal}

{period_text}

Создай ровно {number_of_tasks} конкретных задач,
которые помогут достичь этой цели.

Расположи задачи в логическом порядке:
от того, что нужно сделать сначала,
до завершающего этапа.

Для каждой задачи укажи:

- title — короткое название;
- description — конкретное описание;
- priority — только low, medium или high.

Верни ТОЛЬКО JSON.
Не используй Markdown.
Не добавляй никакой текст до или после JSON.

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
                        "Создавай практичные и конкретные задачи. "
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

    content = response["message"]["content"]

    try:
        data = json.loads(content)

    except json.JSONDecodeError:
        raise RuntimeError(
            "AI вернул некорректный JSON"
        )

    try:
        result = AITaskGenerateResponse.model_validate(
            data
        )

    except Exception as error:
        raise RuntimeError(
            f"AI вернул данные неверного формата: {error}"
        )

    if len(result.tasks) != number_of_tasks:
        raise RuntimeError(
            "AI вернул неправильное количество задач"
        )

    result = add_deadlines(
        result=result,
        days=days,
    )

    return result