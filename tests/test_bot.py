from bot.keyboards import (
    main_menu,
    auth_menu,
    priority_menu,
    ai_plan_menu,
    task_actions_menu,
    edit_task_menu,
    delete_confirm_menu,
    replan_instruction_menu,
    replan_preview_menu,
)


def get_reply_button_texts(markup):
    return [
        button.text
        for row in markup.keyboard
        for button in row
    ]


def get_inline_buttons(markup):
    return [
        button
        for row in markup.inline_keyboard
        for button in row
    ]


def test_main_menu():
    markup = main_menu()

    texts = get_reply_button_texts(markup)

    assert "📋 Мои задачи" in texts
    assert "➕ Добавить задачу" in texts
    assert "🤖 AI-план" in texts
    assert "🔄 Перепланировать" in texts
    assert "✅ Выполненные" in texts
    assert "👤 Профиль" in texts


def test_auth_menu():
    markup = auth_menu()

    texts = get_reply_button_texts(markup)

    assert texts == [
        "🔐 Войти в StudyFlow"
    ]


def test_priority_menu():
    markup = priority_menu()

    texts = get_reply_button_texts(markup)

    assert "🟢 Низкий" in texts
    assert "🟡 Средний" in texts
    assert "🔴 Высокий" in texts
    assert "❌ Отмена" in texts


def test_ai_plan_menu():
    markup = ai_plan_menu()

    texts = get_reply_button_texts(markup)

    assert "💾 Сохранить AI-план" in texts
    assert "🔄 Сгенерировать заново" in texts
    assert "❌ Отмена" in texts


def test_task_actions_menu_for_active_task():
    markup = task_actions_menu(
        task_id=15,
        is_done=False,
    )

    buttons = get_inline_buttons(markup)

    callback_data = [
        button.callback_data
        for button in buttons
    ]

    assert "task_complete:15" in callback_data
    assert "task_edit:15" in callback_data
    assert "task_delete:15" in callback_data


def test_task_actions_menu_for_completed_task():
    markup = task_actions_menu(
        task_id=20,
        is_done=True,
    )

    buttons = get_inline_buttons(markup)

    callback_data = [
        button.callback_data
        for button in buttons
    ]

    assert "task_complete:20" not in callback_data
    assert "task_edit:20" in callback_data
    assert "task_delete:20" in callback_data


def test_edit_task_menu():
    markup = edit_task_menu(
        task_id=7
    )

    buttons = get_inline_buttons(markup)

    callback_data = [
        button.callback_data
        for button in buttons
    ]

    assert "task_edit_title:7" in callback_data
    assert "task_edit_description:7" in callback_data
    assert "task_edit_priority:7" in callback_data
    assert "task_edit_deadline:7" in callback_data
    assert "task_edit_cancel:7" in callback_data


def test_delete_confirm_menu():
    markup = delete_confirm_menu(
        task_id=12
    )

    buttons = get_inline_buttons(markup)

    callback_data = [
        button.callback_data
        for button in buttons
    ]

    assert "task_delete_confirm:12" in callback_data
    assert "task_delete_cancel:12" in callback_data


def test_replan_instruction_menu():
    markup = replan_instruction_menu()

    texts = get_reply_button_texts(markup)

    assert "⏭ Без пожеланий" in texts
    assert "❌ Отмена" in texts


def test_replan_preview_menu():
    markup = replan_preview_menu()

    texts = get_reply_button_texts(markup)

    assert "✅ Применить новый план" in texts
    assert "🔄 Пересчитать план" in texts
    assert "❌ Отмена" in texts