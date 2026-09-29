from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

def main_menu():
    keyboard = [
        [
            KeyboardButton(text="📋 Мои задачи"),
            KeyboardButton(text="➕ Добавить задачу"),
        ],
        [
            KeyboardButton(text="🤖 AI-план"),
            KeyboardButton(text="🔄 Перепланировать"),
        ],
        [
            KeyboardButton(text="✅ Выполненные"),
            KeyboardButton(text="👤 Профиль"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие 👇",
    )

def auth_menu():
    keyboard = [
        [
            KeyboardButton(text="🔐 Войти в StudyFlow"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Войдите в аккаунт 👇",
    )

def priority_menu():
    keyboard = [
        [
            KeyboardButton(text="🟢 Низкий"),
            KeyboardButton(text="🟡 Средний"),
            KeyboardButton(text="🔴 Высокий"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите приоритет 👇",
    )

def cancel_menu():
    keyboard = [
        [
            KeyboardButton(text="❌ Отмена"),
        ]
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def description_menu():
    keyboard = [
        [
            KeyboardButton(text="⏭ Без описания"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def deadline_menu():
    keyboard = [
        [
            KeyboardButton(text="⏭ Без дедлайна"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def ai_plan_menu():
    keyboard = [
        [
            KeyboardButton(text="💾 Сохранить AI-план"),
        ],
        [
            KeyboardButton(text="🔄 Сгенерировать заново"),
        ],
        [
            KeyboardButton(text="❌ Отмена"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )

def task_actions_menu(
    task_id: int,
    is_done: bool = False,
):
    first_row = []

    if not is_done:
        first_row.append(
            InlineKeyboardButton(
                text="✅ Выполнить",
                callback_data=f"task_complete:{task_id}",
            )
        )

    first_row.append(
        InlineKeyboardButton(
            text="✏️ Изменить",
            callback_data=f"task_edit:{task_id}",
        )
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            first_row,
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"task_delete:{task_id}",
                )
            ],
        ]
    )

def edit_task_menu(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Название",
                    callback_data=f"task_edit_title:{task_id}",
                ),
                InlineKeyboardButton(
                    text="📄 Описание",
                    callback_data=f"task_edit_description:{task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Приоритет",
                    callback_data=f"task_edit_priority:{task_id}",
                ),
                InlineKeyboardButton(
                    text="📅 Дедлайн",
                    callback_data=f"task_edit_deadline:{task_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Закрыть",
                    callback_data=f"task_edit_cancel:{task_id}",
                ),
            ],
        ]
    )


def delete_confirm_menu(task_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data=f"task_delete_confirm:{task_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=f"task_delete_cancel:{task_id}",
                ),
            ]
        ]
    )

def replan_instruction_menu():
    keyboard = [
        [
            KeyboardButton(
                text="⏭ Без пожеланий"
            ),
        ],
        [
            KeyboardButton(
                text="❌ Отмена"
            ),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def replan_preview_menu():
    keyboard = [
        [
            KeyboardButton(
                text="✅ Применить новый план"
            ),
        ],
        [
            KeyboardButton(
                text="🔄 Пересчитать план"
            ),
        ],
        [
            KeyboardButton(
                text="❌ Отмена"
            ),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )