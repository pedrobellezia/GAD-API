# import uuid
#
# import pytest
#
#
# @pytest.mark.asyncio
# async def test_post_client(client):
#     """Test creating a new client."""
#     # First, create an agency
#     agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
#     agency_response = client.post("/agency", json=agency_data)
#     assert agency_response.status_code == 200
#     agency_id = agency_response.json()["id"]
#
#     # Create a user
#     user_data = {
#         "name": "Test User",
#         "email": "test@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user_response = client.post("/user", json=user_data)
#     assert user_response.status_code == 200
#     user_id = user_response.json()["id"]
#
#     # Create a client
#     client_data = {"id": user_id, "agencyId": agency_id}
#     response = client.post("/client", json=client_data)
#
#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == user_id
#     assert data["agencyId"] == agency_id
#
#
# @pytest.mark.asyncio
# async def test_post_client_invalid_user_id(client):
#     """Test creating a client with an invalid user ID."""
#     # Create an agency
#     agency_data = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
#     agency_response = client.post("/agency", json=agency_data)
#     assert agency_response.status_code == 200
#     agency_id = agency_response.json()["id"]
#
#     # Try to create a client with non-existent user
#     invalid_user_id = str(uuid.uuid4())
#     client_data = {"id": invalid_user_id, "agencyId": agency_id}
#     response = client.post("/client", json=client_data)
#
#     # Should fail because user doesn't exist
#     assert response.status_code >= 400
#
#
# @pytest.mark.asyncio
# async def test_post_client_invalid_agency_id(client):
#     """Test creating a client with an invalid agency ID."""
#     # Create a user
#     user_data = {
#         "name": "Test User",
#         "email": "test@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user_response = client.post("/user", json=user_data)
#     assert user_response.status_code == 200
#     user_id = user_response.json()["id"]
#
#     # Try to create a client with non-existent agency
#     invalid_agency_id = str(uuid.uuid4())
#     client_data = {"id": user_id, "agencyId": invalid_agency_id}
#     response = client.post("/client", json=client_data)
#
#     # Should fail because agency doesn't exist
#     assert response.status_code >= 400
#
#
# @pytest.mark.asyncio
# async def test_get_clients_empty(client):
#     """Test getting clients when none exist."""
#     response = client.get("/client")
#
#     assert response.status_code == 200
#     data = response.json()
#     assert data is None or data == []
#
#
# @pytest.mark.asyncio
# async def test_get_clients_with_data(client):
#     """Test getting clients after creating some."""
#     # Create agency
#     agency = {"name": "Agency 1", "cnpj": "11.111.111/0001-90"}
#     agency_response = client.post("/agency", json=agency)
#     agency_id = agency_response.json()["id"]
#
#     # Create first user and client
#     user1 = {
#         "name": "Client One",
#         "email": "client1@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user1_response = client.post("/user", json=user1)
#     user1_id = user1_response.json()["id"]
#
#     client_data1 = {"id": user1_id, "agencyId": agency_id}
#     client.post("/client", json=client_data1)
#
#     # Create second user and client
#     user2 = {
#         "name": "Client Two",
#         "email": "client2@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user2_response = client.post("/user", json=user2)
#     user2_id = user2_response.json()["id"]
#
#     client_data2 = {"id": user2_id, "agencyId": agency_id}
#     client.post("/client", json=client_data2)
#
#     # Get all clients
#     response = client.get("/client")
#
#     assert response.status_code == 200
#     data = response.json()
#     assert isinstance(data, list)
#     assert len(data) == 2
#
#
# @pytest.mark.asyncio
# async def test_get_clients_filter_by_agency_name(client):
#     """Test filtering clients by agency name."""
#     # Create agencies
#     agency1 = {"name": "Tech Agency", "cnpj": "11.111.111/0001-90"}
#     agency1_response = client.post("/agency", json=agency1)
#     agency1_id = agency1_response.json()["id"]
#
#     agency2 = {"name": "Design Agency", "cnpj": "22.222.222/0001-90"}
#     agency2_response = client.post("/agency", json=agency2)
#     agency2_id = agency2_response.json()["id"]
#
#     # Create users
#     user1 = {
#         "name": "User One",
#         "email": "user1@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user1_response = client.post("/user", json=user1)
#     user1_id = user1_response.json()["id"]
#
#     user2 = {
#         "name": "User Two",
#         "email": "user2@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user2_response = client.post("/user", json=user2)
#     user2_id = user2_response.json()["id"]
#
#     # Create clients
#     client.post("/client", json={"id": user1_id, "agencyId": agency1_id})
#     client.post("/client", json={"id": user2_id, "agencyId": agency2_id})
#
#     # Filter by agency name
#     response = client.get("/client", params={"agency_name": "Tech"})
#
#     assert response.status_code == 200
#     data = response.json()
#     assert isinstance(data, list)
#     # Should have at least one client from Tech Agency
#     if data:
#         assert len(data) >= 1
#
#
# @pytest.mark.asyncio
# async def test_get_clients_pagination(client):
#     """Test pagination of clients."""
#     # Create agency
#     agency = {"name": "Agency", "cnpj": "11.111.111/0001-90"}
#     agency_response = client.post("/agency", json=agency)
#     agency_id = agency_response.json()["id"]
#
#     # Create multiple clients
#     for i in range(1, 6):
#         user = {
#             "name": f"Client {i}",
#             "email": f"client{i}@example.com",
#             "type": "client",
#             "pswd": "password123",
#         }
#         user_response = client.post("/user", json=user)
#         user_id = user_response.json()["id"]
#         client.post("/client", json={"id": user_id, "agencyId": agency_id})
#
#     # Get first page
#     response = client.get("/client", params={"skip": 0, "limit": 2})
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) <= 2
#
#     # Get second page
#     response = client.get("/client", params={"skip": 2, "limit": 2})
#     assert response.status_code == 200
#     data = response.json()
#     assert len(data) <= 2
#
#
# @pytest.mark.asyncio
# async def test_get_client_by_id(client):
#     """Test retrieving a single client by ID."""
#     # Create agency
#     agency = {"name": "Test Agency", "cnpj": "12.345.678/0001-90"}
#     agency_response = client.post("/agency", json=agency)
#     agency_id = agency_response.json()["id"]
#
#     # Create user
#     user_data = {
#         "name": "Test User",
#         "email": "test@example.com",
#         "type": "client",
#         "pswd": "password123",
#     }
#     user_response = client.post("/user", json=user_data)
#     user_id = user_response.json()["id"]
#
#     # Create client
#     client_data = {"id": user_id, "agencyId": agency_id}
#     create_response = client.post("/client", json=client_data)
#     assert create_response.status_code == 200
#
#     # Get client by ID
#     response = client.get(f"/client/{user_id}")
#
#     assert response.status_code == 200
#     data = response.json()
#     assert data["id"] == user_id
#     assert data["agencyId"] == agency_id
#
#
# @pytest.mark.asyncio
# async def test_get_client_by_invalid_id(client):
#     """Test retrieving a client with an invalid ID."""
#     invalid_id = str(uuid.uuid4())
#
#     response = client.get(f"/client/{invalid_id}")
#
#     assert response.status_code == 200
#     data = response.json()
#     assert data is None
