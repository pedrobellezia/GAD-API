import uuid

import pytest


async def _create_user(client):
    email = f"user-{uuid.uuid4()}@example.com"
    payload = {
        "name": "User Test",
        "email": email,
        "type": "admin",
        "avatar": "avatar.png",
        "pswd": "secret123",
    }

    create_resp = await client.post("/user", json=payload)
    assert create_resp.status_code == 202
    return email



async def test_route_post_user(client):
    await _create_user(client)



async def test_route_get_users(client):
    email = await _create_user(client)

    list_resp = await client.get("/user", params={"email": email})
    assert list_resp.status_code == 200
    users = list_resp.json() or []
    assert len(users) == 1
    assert users[0]["email"] == email



async def test_route_get_user_by_id(client):
    email = await _create_user(client)

    list_resp = await client.get("/user", params={"email": email})
    assert list_resp.status_code == 200
    users = list_resp.json() or []
    assert len(users) == 1

    user_id = users[0]["id"]
    get_resp = await client.get(f"/user/{user_id}")
    assert get_resp.status_code == 200
    user = get_resp.json()
    assert user["id"] == user_id
    assert user["email"] == email
