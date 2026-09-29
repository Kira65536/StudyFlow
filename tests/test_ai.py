from datetime import (
    datetime,
    timezone,
)

from schemas import (
    AIGeneratedTask,
    AITaskGenerateResponse,
    AIReplannedTask,
    AIReplanResponse,
)
# HELPERS

def register_and_login(client):

    client.post(
        "/register",
        json={
            "username": "aiuser",
            "email": "ai@example.com",
            "password": "12345678",
        },
    )

    response = client.post(
        "/login",
        json={
            "email": "ai@example.com",
            "password": "12345678",
        },
    )

    token = response.json()[
        "access_token"
    ]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_task(client, headers):

    response = client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Повторить FastAPI",
            "description": "Разобраться с Depends",
            "priority": "medium",
            "status": "todo",
            "deadline": None,
        },
    )

    return response.json()

# AI — GENERATE TASKS

def test_generate_ai_tasks(
    client,
    monkeypatch,
):

    headers = register_and_login(
        client
    )

    def fake_generate_tasks(
        goal,
        number_of_tasks,
        days=None,
    ):

        return AITaskGenerateResponse(
            goal=goal,
            tasks=[
                AIGeneratedTask(
                    title="Повторить Python",
                    description="Повторить функции и классы",
                    priority="high",
                    deadline=datetime(
                        2026,
                        9,
                        26,
                        12,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
                AIGeneratedTask(
                    title="Повторить SQL",
                    description="Повторить JOIN",
                    priority="medium",
                    deadline=datetime(
                        2026,
                        9,
                        28,
                        12,
                        0,
                        tzinfo=timezone.utc,
                    ),
                ),
            ],
        )

    monkeypatch.setattr(
        "routers.ai.generate_tasks_with_ai",
        fake_generate_tasks,
    )

    response = client.post(
        "/ai/generate-tasks",
        headers=headers,
        json={
            "goal": (
                "Подготовиться к собеседованию "
                "Python backend разработчика"
            ),
            "number_of_tasks": 2,
            "days": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["tasks"]) == 2

    assert (
        data["tasks"][0]["title"]
        == "Повторить Python"
    )

    assert (
        data["tasks"][0]["priority"]
        == "high"
    )
# AI — SAVE TASKS
def test_save_ai_tasks(client):

    headers = register_and_login(
        client
    )

    response = client.post(
        "/ai/save-tasks",
        headers=headers,
        json={
            "tasks": [
                {
                    "title": "Повторить Python",
                    "description": "Функции и классы",
                    "priority": "high",
                    "deadline": (
                        "2026-09-26T12:00:00Z"
                    ),
                },
                {
                    "title": "Повторить SQL",
                    "description": "JOIN и GROUP BY",
                    "priority": "medium",
                    "deadline": (
                        "2026-09-28T12:00:00Z"
                    ),
                },
            ]
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["saved_count"] == 2
    assert len(data["tasks"]) == 2

    # Дополнительно проверяем, что задачи реально появились в БД
    tasks_response = client.get(
        "/tasks",
        headers=headers,
    )

    tasks = tasks_response.json()

    assert len(tasks) == 2

# AI — REPLAN

def test_ai_replan(
    client,
    monkeypatch,
):

    headers = register_and_login(
        client
    )

    task = create_task(
        client,
        headers,
    )

    task_id = task["id"]

    def fake_replan(
        tasks,
        days,
        instruction=None,
    ):

        return AIReplanResponse(
            days=days,
            tasks=[
                AIReplannedTask(
                    task_id=task_id,
                    title="Повторить FastAPI",
                    description="Разобраться с Depends",
                    priority="high",
                    status="todo",
                    deadline=datetime(
                        2026,
                        9,
                        27,
                        12,
                        0,
                        tzinfo=timezone.utc,
                    ),
                )
            ],
        )

    monkeypatch.setattr(
        "routers.ai.replan_tasks_with_ai",
        fake_replan,
    )

    response = client.post(
        "/ai/replan",
        headers=headers,
        json={
            "days": 5,
            "instruction": (
                "Сначала самое важное"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["days"] == 5
    assert len(data["tasks"]) == 1

    assert (
        data["tasks"][0]["task_id"]
        == task_id
    )

    assert (
        data["tasks"][0]["priority"]
        == "high"
    )



# AI — APPLY REPLAN

def test_apply_replan(client):

    headers = register_and_login(
        client
    )

    task = create_task(
        client,
        headers,
    )

    task_id = task["id"]

    response = client.post(
        "/ai/apply-replan",
        headers=headers,
        json={
            "tasks": [
                {
                    "task_id": task_id,
                    "priority": "high",
                    "deadline": (
                        "2026-09-29T12:00:00Z"
                    ),
                }
            ]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["updated_count"] == 1

    assert (
        data["tasks"][0]["priority"]
        == "high"
    )

    # Проверяем, что изменения действительно сохранились
    task_response = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    updated_task = (
        task_response.json()
    )

    assert (
        updated_task["priority"]
        == "high"
    )

    assert (
        updated_task["deadline"]
        is not None
    )
# AI БЕЗ АВТОРИЗАЦИИ

def test_ai_without_token(client):

    response = client.post(
        "/ai/generate-tasks",
        json={
            "goal": "Изучить FastAPI",
            "number_of_tasks": 3,
            "days": 7,
        },
    )

    assert response.status_code == 401