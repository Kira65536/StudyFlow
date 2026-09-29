def register_user(client):
    return client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345678",
        },
    )


def login_user(client):
    return client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "12345678",
        },
    )


def test_register(client):
    response = register_user(
        client
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"

    # Пароль API возвращать не должен
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email(client):
    register_user(
        client
    )

    response = client.post(
        "/register",
        json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 409


def test_login(client):
    register_user(
        client
    )

    response = login_user(
        client
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    register_user(
        client
    )

    response = client.post(
        "/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_me(client):
    register_user(
        client
    )

    login_response = login_user(
        client
    )

    token = login_response.json()[
        "access_token"
    ]

    response = client.get(
        "/me",
        headers={
            "Authorization": (
                f"Bearer {token}"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


def test_me_without_token(client):
    response = client.get(
        "/me"
    )

    assert response.status_code == 401