import uuid



async def _create_agency(client):
    cnpj = f"{uuid.uuid4().int % 10**14:014d}"
    payload = {
        "cnpj": cnpj,
        "user": {
            "name": "Agency User",
            "email": f"agency-{uuid.uuid4()}@example.com",
            "type": "agency",
            "avatar": "logo.png",
            "pswd": "secret123",
        },
    }

    create_resp = await client.post("/agency", json=payload)
    assert create_resp.status_code == 202
    return cnpj


async def test_route_post_agency(client):
    await _create_agency(client)


async def test_route_get_agencies(client):
    cnpj = await _create_agency(client)

    list_resp = await client.get("/agency", params={"cnpj": cnpj})
    assert list_resp.status_code == 200
    agencies = list_resp.json() or []
    assert len(agencies) == 1
    assert agencies[0]["cnpj"] == cnpj


async def test_route_get_agency_by_id(client):
    cnpj = await _create_agency(client)

    list_resp = await client.get("/agency", params={"cnpj": cnpj})
    assert list_resp.status_code == 200
    agencies = list_resp.json() or []
    assert len(agencies) == 1

    agency_id = agencies[0]["id"]
    get_resp = await client.get(f"/agency/{agency_id}")
    assert get_resp.status_code == 200
    agency = get_resp.json()
    assert agency["id"] == agency_id
    assert agency["cnpj"] == cnpj
