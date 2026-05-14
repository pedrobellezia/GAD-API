import uuid



async def _create_agency(client):
    cnpj = f"{uuid.uuid4().int % 10**14:014d}"
    payload = {
        "cnpj": cnpj,
        "user": {
            "name": "Agency For Client",
            "email": f"agency-client-{uuid.uuid4()}@example.com",
            "type": "agency",
            "avatar": "logo.png",
            "pswd": "secret123",
        },
    }

    create_resp = await client.post("/agency", json=payload)
    assert create_resp.status_code == 202

    list_resp = await client.get("/agency", params={"cnpj": cnpj})
    assert list_resp.status_code == 200
    agencies = list_resp.json() or []
    assert len(agencies) == 1
    return agencies[0]


async def _create_client(client):
    agency = await _create_agency(client)
    payload = {
        "agency_id": agency["id"],
        "user": {
            "name": "Client User",
            "email": f"client-{uuid.uuid4()}@example.com",
            "type": "client",
            "avatar": "logo.png",
            "pswd": "secret123",
        },
    }

    create_resp = await client.post("/client", json=payload)
    assert create_resp.status_code == 202
    return agency


async def test_route_post_client(client):
    await _create_client(client)


async def test_route_get_clients(client):
    agency = await _create_client(client)

    list_resp = await client.get("/client", params={"agency_cnpj": agency["cnpj"]})
    assert list_resp.status_code == 200
    clients = list_resp.json() or []
    assert len(clients) == 1


async def test_route_get_client_by_id(client):
    agency = await _create_client(client)

    list_resp = await client.get("/client", params={"agency_cnpj": agency["cnpj"]})
    assert list_resp.status_code == 200
    clients = list_resp.json() or []
    assert len(clients) == 1

    client_id = clients[0]["id"]
    get_resp = await client.get(f"/client/{client_id}")
    assert get_resp.status_code == 200
    client_data = get_resp.json()
    assert client_data["id"] == client_id
    assert client_data["agency"]["id"] == agency["id"]
