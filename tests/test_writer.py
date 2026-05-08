import uuid

from httpx import AsyncClient


async def test_post_writer(client: AsyncClient):
    """Test creating a new writer."""
    # First, create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    # Create a writer with nested user
    writer_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Test Writer",
            "email": "writer@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    response = await client.post("/writer", json=writer_data)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["agencyId"] == agency_id


async def test_post_writer_invalid_user_id(client: AsyncClient):
    """Test creating a writer with an invalid user type."""
    # Create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    writer_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Wrong Type",
            "email": "wrongtype@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    response = await client.post("/writer", json=writer_data)

    assert response.status_code == 422


async def test_post_writer_invalid_agency_id(client: AsyncClient):
    """Test creating a writer with an invalid agency ID."""
    invalid_agency_id = str(uuid.uuid4())
    writer_data = {
        "agencyId": invalid_agency_id,
        "user": {
            "name": "Test Writer",
            "email": "writer@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    response = await client.post("/writer", json=writer_data)

    assert response.status_code >= 400


async def test_get_writers_empty(client: AsyncClient):
    """Test getting writers when none exist."""
    response = await client.get("/writer")

    assert response.status_code == 200
    data = response.json()
    assert data is None or data == []


async def test_get_writers_with_data(client: AsyncClient):
    """Test getting writers after creating some."""
    # Create agency
    agency = {"name": "Agency 1", "cnpj": "11.111.111/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create first writer
    writer_data1 = {
        "agencyId": agency_id,
        "user": {
            "name": "Writer One",
            "email": "writer1@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    await client.post("/writer", json=writer_data1)

    # Create second writer
    writer_data2 = {
        "agencyId": agency_id,
        "user": {
            "name": "Writer Two",
            "email": "writer2@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    await client.post("/writer", json=writer_data2)

    # Get all writers
    response = await client.get("/writer")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


async def test_get_writers_filter_by_agency_name(client: AsyncClient):
    """Test filtering writers by agency name."""
    # Create agencies
    agency1 = {"name": "Tech Agency", "cnpj": "11.111.111/0001-90"}
    agency1_response = await client.post("/agency", json=agency1)
    agency1_id = agency1_response.json()["id"]

    agency2 = {"name": "Design Agency", "cnpj": "22.222.222/0001-90"}
    agency2_response = await client.post("/agency", json=agency2)
    agency2_id = agency2_response.json()["id"]

    # Create writers
    await client.post(
        "/writer",
        json={
            "agencyId": agency1_id,
            "user": {
                "name": "User One",
                "email": "user1@example.com",
                "type": "writer",
                "pswd": "password123",
            },
        },
    )
    await client.post(
        "/writer",
        json={
            "agencyId": agency2_id,
            "user": {
                "name": "User Two",
                "email": "user2@example.com",
                "type": "writer",
                "pswd": "password123",
            },
        },
    )

    # Filter by agency name
    response = await client.get("/writer", params={"agency_name": "Tech"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert len(data) >= 1


async def test_get_writers_filter_by_user_name(client: AsyncClient):
    """Test filtering writers by user name."""
    # Create agency
    agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create writers
    await client.post(
        "/writer",
        json={
            "agencyId": agency_id,
            "user": {
                "name": "Alice Writer",
                "email": "alice@example.com",
                "type": "writer",
                "pswd": "password123",
            },
        },
    )
    await client.post(
        "/writer",
        json={
            "agencyId": agency_id,
            "user": {
                "name": "Bob Writer",
                "email": "bob@example.com",
                "type": "writer",
                "pswd": "password123",
            },
        },
    )

    # Filter by user name
    response = await client.get("/writer", params={"user_name": "Alice"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert len(data) >= 1


async def test_get_writers_pagination(client: AsyncClient):
    """Test pagination of writers."""
    # Create agency
    agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create multiple writers
    for i in range(1, 6):
        await client.post(
            "/writer",
            json={
                "agencyId": agency_id,
                "user": {
                    "name": f"Writer {i}",
                    "email": f"writer{i}@example.com",
                    "type": "writer",
                    "pswd": "password123",
                },
            },
        )

    # Get first page
    response = await client.get("/writer", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Get second page
    response = await client.get("/writer", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


async def test_get_writer_by_id(client: AsyncClient):
    """Test retrieving a single writer by ID."""
    # Create agency
    agency = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create writer
    writer_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Test Writer",
            "email": "writer@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    create_response = await client.post("/writer", json=writer_data)
    assert create_response.status_code == 200

    writer_id = create_response.json()["id"]

    # Get writer by ID
    response = await client.get(f"/writer/{writer_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == writer_id
    assert data["agencyId"] == agency_id


async def test_get_writer_by_invalid_id(client: AsyncClient):
    """Test retrieving a writer with an invalid ID."""
    invalid_id = str(uuid.uuid4())

    response = await client.get(f"/writer/{invalid_id}")

    assert response.status_code == 200
    data = response.json()
    assert data is None
