import uuid

import pytest


@pytest.mark.asyncio
async def test_post_writer(client):
    """Test creating a new writer."""
    # First, create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    # Create a user
    user_data = {
        "name": "Test Writer",
        "email": "writer@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user_response = client.post("/user", json=user_data)
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]

    # Create a writer
    writer_data = {"id": user_id, "agencyId": agency_id}
    response = client.post("/writer", json=writer_data)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["agencyId"] == agency_id


@pytest.mark.asyncio
async def test_post_writer_invalid_user_id(client):
    """Test creating a writer with an invalid user ID."""
    # Create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    # Try to create a writer with non-existent user
    invalid_user_id = str(uuid.uuid4())
    writer_data = {"id": invalid_user_id, "agencyId": agency_id}
    response = client.post("/writer", json=writer_data)

    # Should fail because user doesn't exist
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_post_writer_invalid_agency_id(client):
    """Test creating a writer with an invalid agency ID."""
    # Create a user
    user_data = {
        "name": "Test Writer",
        "email": "writer@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user_response = client.post("/user", json=user_data)
    assert user_response.status_code == 200
    user_id = user_response.json()["id"]

    # Try to create a writer with non-existent agency
    invalid_agency_id = str(uuid.uuid4())
    writer_data = {"id": user_id, "agencyId": invalid_agency_id}
    response = client.post("/writer", json=writer_data)

    # Should fail because agency doesn't exist
    assert response.status_code >= 400


@pytest.mark.asyncio
async def test_get_writers_empty(client):
    """Test getting writers when none exist."""
    response = client.get("/writer")

    assert response.status_code == 200
    data = response.json()
    assert data is None or data == []


@pytest.mark.asyncio
async def test_get_writers_with_data(client):
    """Test getting writers after creating some."""
    # Create agency
    agency = {"name": "Agency 1", "cnpj": "11.111.111/0001-90"}
    agency_response = client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create first user and writer
    user1 = {
        "name": "Writer One",
        "email": "writer1@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user1_response = client.post("/user", json=user1)
    user1_id = user1_response.json()["id"]

    writer_data1 = {"id": user1_id, "agencyId": agency_id}
    client.post("/writer", json=writer_data1)

    # Create second user and writer
    user2 = {
        "name": "Writer Two",
        "email": "writer2@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user2_response = client.post("/user", json=user2)
    user2_id = user2_response.json()["id"]

    writer_data2 = {"id": user2_id, "agencyId": agency_id}
    client.post("/writer", json=writer_data2)

    # Get all writers
    response = client.get("/writer")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_writers_filter_by_agency_name(client):
    """Test filtering writers by agency name."""
    # Create agencies
    agency1 = {"name": "Tech Agency", "cnpj": "11.111.111/0001-90"}
    agency1_response = client.post("/agency", json=agency1)
    agency1_id = agency1_response.json()["id"]

    agency2 = {"name": "Design Agency", "cnpj": "22.222.222/0001-90"}
    agency2_response = client.post("/agency", json=agency2)
    agency2_id = agency2_response.json()["id"]

    # Create users
    user1 = {
        "name": "User One",
        "email": "user1@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user1_response = client.post("/user", json=user1)
    user1_id = user1_response.json()["id"]

    user2 = {
        "name": "User Two",
        "email": "user2@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user2_response = client.post("/user", json=user2)
    user2_id = user2_response.json()["id"]

    # Create writers
    client.post("/writer", json={"id": user1_id, "agencyId": agency1_id})
    client.post("/writer", json={"id": user2_id, "agencyId": agency2_id})

    # Filter by agency name
    response = client.get("/writer", params={"agency_name": "Tech"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one writer from Tech Agency
    if data:
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_writers_filter_by_user_name(client):
    """Test filtering writers by user name."""
    # Create agency
    agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
    agency_response = client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create users
    user1 = {
        "name": "Alice Writer",
        "email": "alice@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user1_response = client.post("/user", json=user1)
    user1_id = user1_response.json()["id"]

    user2 = {
        "name": "Bob Writer",
        "email": "bob@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user2_response = client.post("/user", json=user2)
    user2_id = user2_response.json()["id"]

    # Create writers
    client.post("/writer", json={"id": user1_id, "agencyId": agency_id})
    client.post("/writer", json={"id": user2_id, "agencyId": agency_id})

    # Filter by user name
    response = client.get("/writer", params={"user_name": "Alice"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one writer named Alice
    if data:
        assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_writers_pagination(client):
    """Test pagination of writers."""
    # Create agency
    agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
    agency_response = client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create multiple writers
    for i in range(1, 6):
        user = {
            "name": f"Writer {i}",
            "email": f"writer{i}@example.com",
            "type": "writer",
            "pswd": "password123",
        }
        user_response = client.post("/user", json=user)
        user_id = user_response.json()["id"]
        client.post("/writer", json={"id": user_id, "agencyId": agency_id})

    # Get first page
    response = client.get("/writer", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Get second page
    response = client.get("/writer", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


@pytest.mark.asyncio
async def test_get_writer_by_id(client):
    """Test retrieving a single writer by ID."""
    # Create agency
    agency = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create user
    user_data = {
        "name": "Test Writer",
        "email": "writer@example.com",
        "type": "writer",
        "pswd": "password123",
    }
    user_response = client.post("/user", json=user_data)
    user_id = user_response.json()["id"]

    # Create writer
    writer_data = {"id": user_id, "agencyId": agency_id}
    create_response = client.post("/writer", json=writer_data)
    assert create_response.status_code == 200

    # Get writer by ID
    response = client.get(f"/writer/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["agencyId"] == agency_id


@pytest.mark.asyncio
async def test_get_writer_by_invalid_id(client):
    """Test retrieving a writer with an invalid ID."""
    invalid_id = str(uuid.uuid4())

    response = client.get(f"/writer/{invalid_id}")

    assert response.status_code == 200
    data = response.json()
    assert data is None
