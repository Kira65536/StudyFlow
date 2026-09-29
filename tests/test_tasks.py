def register_and_login(client):
    """
    Создаёт тестового пользователя
    и возвращает заголовок авторизации.
    """

    client.post(
        "/register",
        json={
            "username": "taskuser",
            "email": "tasks@example.com",
            "password": "12345678",
        },
    )

    response = client.post(
        "/login",
        json={
            "email": "tasks@example.com",
            "password": "12345678",
        },
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_task(client, headers):
    """
    Создаёт тестовую задачу.
    """

    return client.post(
        "/tasks",
        headers=headers,
        json={
            "title": "Изучить FastAPI",
            "description": "Повторить Depends и routers",
            "priority": "high",
            "status": "todo",
            "deadline": None,
        },
    )

# СОЗДАНИЕ

def test_create_task(client):
    headers = register_and_login(client)

    response = create_task(
        client,
        headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Изучить FastAPI"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert data["completed"] is False


# ПОЛУЧЕНИЕ ВСЕХ ЗАДАЧ

def test_get_tasks(client):
    headers = register_and_login(client)

    create_task(
        client,
        headers,
    )

    response = client.get(
        "/tasks",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Изучить FastAPI"


# ПОЛУЧЕНИЕ ОДНОЙ ЗАДАЧИ

def test_get_task(client):
    headers = register_and_login(client)

    create_response = create_task(
        client,
        headers,
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id


#PATCH

def test_patch_task(client):
    headers = register_and_login(client)

    create_response = create_task(
        client,
        headers,
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        headers=headers,
        json={
            "status": "done"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "done"
    assert data["completed"] is True

# PUT

def test_update_task(client):
    headers = register_and_login(client)

    create_response = create_task(
        client,
        headers,
    )

    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Повторить SQL",
            "description": "JOIN и GROUP BY",
            "priority": "medium",
            "status": "in_progress",
            "deadline": None,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Повторить SQL"
    assert data["priority"] == "medium"
    assert data["status"] == "in_progress"


# DELETE

def test_delete_task(client):
    headers = register_and_login(client)

    create_response = create_task(
        client,
        headers,
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    assert data["task_id"] == task_id

    # Проверяем, что задача действительно исчезла
    get_response = client.get(
        f"/tasks/{task_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


# БЕЗ АВТОРИЗАЦИИ

def test_tasks_without_token(client):
    response = client.get(
        "/tasks"
    )

    assert response.status_code == 401

# ПОЛЬЗОВАТЕЛЬ НЕ ВИДИТ ЧУЖИЕ ЗАДАЧИ
def test_user_cannot_access_other_user_task(client):

    # Первый пользователь
    client.post(
        "/register",
        json={
            "username": "user_one",
            "email": "one@example.com",
            "password": "12345678",
        },
    )

    login_one = client.post(
        "/login",
        json={
            "email": "one@example.com",
            "password": "12345678",
        },
    )

    token_one = login_one.json()[
        "access_token"
    ]

    headers_one = {
        "Authorization": f"Bearer {token_one}"
    }

    task_response = client.post(
        "/tasks",
        headers=headers_one,
        json={
            "title": "Секретная задача",
            "description": "",
            "priority": "medium",
            "status": "todo",
            "deadline": None,
        },
    )

    task_id = task_response.json()["id"]

    # Второй пользователь
    client.post(
        "/register",
        json={
            "username": "user_two",
            "email": "two@example.com",
            "password": "12345678",
        },
    )

    login_two = client.post(
        "/login",
        json={
            "email": "two@example.com",
            "password": "12345678",
        },
    )

    token_two = login_two.json()[
        "access_token"
    ]

    headers_two = {
        "Authorization": f"Bearer {token_two}"
    }

    response = client.get(
        f"/tasks/{task_id}",
        headers=headers_two,
    )

    assert response.status_code == 404