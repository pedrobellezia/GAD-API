import uuid

from httpx import AsyncClient


async def test_post_agency(client: AsyncClient):
    """Test creating a new agency."""
    agency_data = {
        "name": "Test Agency",
        "cnpj": "12.345.678/0001-90",
    }

    response = await client.post("/agency", json=agency_data)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == agency_data["name"]
    assert data["cnpj"] == agency_data["cnpj"]
    assert "id" in data
    assert "created_at" in data


async def test_post_agency_duplicate_cnpj(client: AsyncClient):
    """Test creating agencies with duplicate CNPJ."""
    agency_data = {
        "name": "Test Agency",
        "cnpj": "12.345.678/0001-90",
    }

    # First agency should succeed
    response1 = await client.post("/agency", json=agency_data)
    assert response1.status_code == 200

    # Second agency with same CNPJ should fail
    response2 = await client.post("/agency", json=agency_data)
    assert response2.status_code >= 400


async def test_post_agency_missing_fields(client: AsyncClient):
    """Test creating an agency with missing required fields."""
    agency_data = {"name": "Test Agency"}  # Missing cnpj

    response = await client.post("/agency", json=agency_data)

    assert response.status_code == 422


async def test_get_agencies_empty(client: AsyncClient):
    """Test getting agencies when none exist."""
    response = await client.get("/agency")

    assert response.status_code == 200
    data = response.json()
    assert data is None or data == []


async def test_get_agencies_with_data(client: AsyncClient):
    """Test getting agencies after creating some."""
    # Create first agency
    agency1 = {
        "name": "Agency 1",
        "cnpj": "11.111.111/0001-90",
    }
    response1 = await client.post("/agency", json=agency1)
    assert response1.status_code == 200

    # Create second agency
    agency2 = {
        "name": "Agency 2",
        "cnpj": "22.222.222/0001-90",
    }
    response2 = await client.post("/agency", json=agency2)
    assert response2.status_code == 200

    # Get all agencies
    response = await client.get("/agency")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


async def test_get_agencies_filter_by_name(client: AsyncClient):
    """Test filtering agencies by name."""
    # Create agencies
    agency1 = {"name": "Tech Solutions", "cnpj": "11.111.111/0001-90"}
    agency2 = {"name": "Design Agency", "cnpj": "22.222.222/0001-90"}

    await client.post("/agency", json=agency1)
    await client.post("/agency", json=agency2)

    # Filter by name
    response = await client.get("/agency", params={"name": "Tech"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Tech Solutions"


async def test_get_agencies_filter_by_cnpj(client: AsyncClient):
    """Test filtering agencies by CNPJ."""
    # Create agencies
    agency1 = {"name": "Agency 1", "cnpj": "11.111.111/0001-90"}
    agency2 = {"name": "Agency 2", "cnpj": "22.222.222/0001-90"}

    await client.post("/agency", json=agency1)
    await client.post("/agency", json=agency2)

    # Filter by CNPJ
    response = await client.get("/agency", params={"cnpj": "11.111.111/0001-90"})

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["cnpj"] == "11.111.111/0001-90"


async def test_get_agencies_pagination(client: AsyncClient):
    """Test pagination of agencies."""
    # Create multiple agencies
    agencies = [
        {"name": f"Agency {i}", "cnpj": f"{i:02d}.111.111/0001-90"} for i in range(1, 6)
    ]

    for agency in agencies:
        await client.post("/agency", json=agency)

    # Get first page (limit=2)
    response = await client.get("/agency", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Get second page (limit=2)
    response = await client.get("/agency", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


async def test_get_agency_by_id(client: AsyncClient):
    """Test retrieving a single agency by ID."""
    # Create an agency
    agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
    create_response = await client.post("/agency", json=agency_data)
    assert create_response.status_code == 200

    agency_id = create_response.json()["id"]

    # Get the agency by ID
    response = await client.get(f"/agency/{agency_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agency_id
    assert data["name"] == agency_data["name"]
    assert data["cnpj"] == agency_data["cnpj"]


async def test_get_agency_by_invalid_id(client: AsyncClient):
    """Test retrieving an agency with an invalid ID."""
    invalid_id = str(uuid.uuid4())

    response = await client.get(f"/agency/{invalid_id}")

    assert response.status_code == 200
    data = response.json()
    assert data is None
