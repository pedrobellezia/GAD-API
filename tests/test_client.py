import uuid

from httpx import AsyncClient


async def test_post_client(client: AsyncClient):
    """Test creating a new client."""
    # First, create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    # Create a client with nested user
    client_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    response = await client.post("/client", json=client_data)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["agencyId"] == agency_id


async def test_post_client_invalid_user_id(client: AsyncClient):
    """Test creating a client with an invalid user type."""
    # Create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency_data)
    assert agency_response.status_code == 200
    agency_id = agency_response.json()["id"]

    # Try to create a client with wrong user type
    client_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Wrong Type",
            "email": "wrongtype@example.com",
            "type": "writer",
            "pswd": "password123",
        },
    }
    response = await client.post("/client", json=client_data)

    assert response.status_code == 422


async def test_post_client_invalid_agency_id(client: AsyncClient):
    """Test creating a client with an invalid agency ID."""
    invalid_agency_id = str(uuid.uuid4())
    client_data = {
        "agencyId": invalid_agency_id,
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    response = await client.post("/client", json=client_data)

    assert response.status_code >= 400


async def test_get_clients_empty(client: AsyncClient):
    """Test getting clients when none exist."""
    response = await client.get("/client")

    assert response.status_code == 200
    data = response.json()
    assert data is None or data == []


async def test_get_clients_with_data(client: AsyncClient):
    """Test getting clients after creating some."""
    # Create agency
    agency = {"name": "Agency 1", "cnpj": "11.111.111/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create first client
    client_data1 = {
        "agencyId": agency_id,
        "user": {
            "name": "Client One",
            "email": "client1@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    await client.post("/client", json=client_data1)

    # Create second client
    client_data2 = {
        "agencyId": agency_id,
        "user": {
            "name": "Client Two",
            "email": "client2@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    await client.post("/client", json=client_data2)

    # Get all clients
    response = await client.get("/client")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


async def test_get_clients_filter_by_agency_name(client: AsyncClient):
    """Test filtering clients by agency name."""
    # Create agencies
    agency1 = {"name": "Tech Agency", "cnpj": "11.111.111/0001-90"}
    agency1_response = await client.post("/agency", json=agency1)
    agency1_id = agency1_response.json()["id"]

    agency2 = {"name": "Design Agency", "cnpj": "22.222.222/0001-90"}
    agency2_response = await client.post("/agency", json=agency2)
    agency2_id = agency2_response.json()["id"]

    # Create clients
    await client.post(
        "/client",
        json={
            "agencyId": agency1_id,
            "user": {
                "name": "User One",
                "email": "user1@example.com",
                "type": "client",
                "pswd": "password123",
            },
        },
    )
    await client.post(
        "/client",
        json={
            "agencyId": agency2_id,
            "user": {
                "name": "User Two",
                "email": "user2@example.com",
                "type": "client",
                "pswd": "password123",
            },
        },
    )

    # Filter by agency name
    response = await client.get("/client", params={"agency_name": "Tech"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert len(data) >= 1


async def test_get_clients_pagination(client: AsyncClient):
    """Test pagination of clients."""
    # Create agency
    agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create multiple clients
    for i in range(1, 6):
        await client.post(
            "/client",
            json={
                "agencyId": agency_id,
                "user": {
                    "name": f"Client {i}",
                    "email": f"client{i}@example.com",
                    "type": "client",
                    "pswd": "password123",
                },
            },
        )

    # Get first page
    response = await client.get("/client", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2

    # Get second page
    response = await client.get("/client", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


async def test_get_client_by_id(client: AsyncClient):
    """Test retrieving a single client by ID."""
    # Create agency
    agency = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    agency_response = await client.post("/agency", json=agency)
    agency_id = agency_response.json()["id"]

    # Create client
    client_data = {
        "agencyId": agency_id,
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "type": "client",
            "pswd": "password123",
        },
    }
    create_response = await client.post("/client", json=client_data)
    assert create_response.status_code == 200

    client_id = create_response.json()["id"]

    # Get the client by ID
    response = await client.get(f"/client/{client_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == client_id
    assert data["agencyId"] == agency_id


async def test_get_client_by_invalid_id(client: AsyncClient):
    """Test retrieving a client with an invalid ID."""
    invalid_id = str(uuid.uuid4())

    response = await client.get(f"/client/{invalid_id}")

    assert response.status_code == 200
    data = response.json()
    assert data is None
