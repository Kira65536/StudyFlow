def test_home(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "StudyFlow API"
    assert data["status"] == "running"


def test_health(client):
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }