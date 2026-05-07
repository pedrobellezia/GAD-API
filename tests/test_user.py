import uuid

from httpx import AsyncClient


async def test_post_user(client: AsyncClient):
    """Test creating a new user."""
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "type": "admin",
        "pswd": "password123",
        "avatar": "https://example.com/avatar.jpg",
    }

    response = await client.post("/user", json=user_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == user_data["name"]
    assert data["email"] == user_data["email"]
    assert data["type"] == user_data["type"]
    assert "id" in data
    assert "created_at" in data


async def test_post_user_duplicate_email(client: AsyncClient):
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "type": "client",
        "pswd": "password123",
    }

    response1 = await client.post("/user", json=user_data)
    assert response1.status_code == 200

    response2 = await client.post("/user", json=user_data)
    assert response2.status_code >= 400


async def test_post_user_invalid_type(client: AsyncClient):
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "type": "invalid_type",
        "pswd": "password123",
    }

    response = await client.post("/user", json=user_data)

    assert response.status_code == 422


async def test_post_user_missing_fields(client: AsyncClient):
    """Test creating a user with missing required fields."""
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        # Missing type and pswd
    }

    response = await client.post("/user", json=user_data)

    assert response.status_code == 422


async def test_get_users_empty(client: AsyncClient):
    """Test getting users when none exist."""
    response = await client.get("/user")

    assert response.status_code == 200
    data = response.json()
    assert data is None or data == []


async def test_get_users_with_data(client: AsyncClient):
    """Test getting users after creating some."""
    # Create first user
    user1 = {
        "name": "User One",
        "email": "user1@example.com",
        "type": "admin",
        "pswd": "password123",
    }
    response1 = await client.post("/user", json=user1)
    assert response1.status_code == 200

    # Create second user
    user2 = {
        "name": "User Two",
        "email": "user2@example.com",
        "type": "client",
        "pswd": "password123",
    }
    response2 = await client.post("/user", json=user2)
    assert response2.status_code == 200

    # Get all users
    response = await client.get("/user")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


async def test_get_users_filter_by_name(client: AsyncClient):
    """Test filtering users by name."""
    # Create users
    user1 = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "type": "admin",
        "pswd": "password123",
    }
    user2 = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "type": "writer",
        "pswd": "password123",
    }

    await client.post("/user", json=user1)
    await client.post("/user", json=user2)

    # Filter by name
    response = await client.get("/user", params={"name": "Alice"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Alice Johnson"


async def test_get_users_filter_by_type(client: AsyncClient):
    """Test filtering users by type."""
    # Create users with different types
    user1 = {
        "name": "Admin User",
        "email": "admin@example.com",
        "type": "admin",
        "pswd": "password123",
    }
    user2 = {
        "name": "Client User",
        "email": "client@example.com",
        "type": "client",
        "pswd": "password123",
    }

    await client.post("/user", json=user1)
    await client.post("/user", json=user2)

    # Filter by type
    response = await client.get("/user", params={"type": "admin"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["type"] == "admin"


async def test_get_users_filter_by_email(client: AsyncClient):
    """Test filtering users by email."""
    # Create users
    user1 = {
        "name": "User One",
        "email": "user1@example.com",
        "type": "admin",
        "pswd": "password123",
    }
    user2 = {
        "name": "User Two",
        "email": "user2@example.com",
        "type": "client",
        "pswd": "password123",
    }

    await client.post("/user", json=user1)
    await client.post("/user", json=user2)

    # Filter by email
    response = await client.get("/user", params={"email": "user1@example.com"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["email"] == "user1@example.com"


async def test_get_users_pagination(client: AsyncClient):
    """Test pagination of users."""
    # Create multiple users
    users = [
        {
            "name": f"User {i}",
            "email": f"user{i}@example.com",
            "pswd": "password123",
        }
        for i in range(1, 6)
    ]

    for user in users:
        await client.post("/user", json=user)

    # Get first page (limit=2)
    response = await client.get("/user", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Get second page (limit=2)
    response = await client.get("/user", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


async def test_get_user_by_id(client: AsyncClient):
    """Test retrieving a single user by ID."""
    # Create a user
    user_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "type": "client",
        "pswd": "password123",
    }
    create_response = await client.post("/user", json=user_data)
    assert create_response.status_code == 200

    user_id = create_response.json()["id"]

    # Get the user by ID
    response = await client.get(f"/user/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == user_data["name"]
    assert data["email"] == user_data["email"]


async def test_get_user_by_invalid_id(client: AsyncClient):
    """Test retrieving a user with an invalid ID."""
    invalid_id = str(uuid.uuid4())

    response = await client.get(f"/user/{invalid_id}")

    assert response.status_code == 200
    data = response.json()
    assert data is None
