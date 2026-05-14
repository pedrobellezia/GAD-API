import uuid

import pytest


async def _create_agency(client):
    cnpj = f"{uuid.uuid4().int % 10**14:014d}"
    payload = {
        "cnpj": cnpj,
        "user": {
            "name": "Agency For Writer",
            "email": f"agency-writer-{uuid.uuid4()}@example.com",
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


async def _create_writer(client):
    agency = await _create_agency(client)
    payload = {
        "agency_id": agency["id"],
        "user": {
            "name": "Writer User",
            "email": f"writer-{uuid.uuid4()}@example.com",
            "type": "writer",
            "avatar": "logo.png",
            "pswd": "secret123",
        },
    }

    create_resp = await client.post("/writer", json=payload)
    assert create_resp.status_code == 202
    return agency


async def test_route_post_writer(client):
    await _create_writer(client)


async def test_route_get_writers(client):
    agency = await _create_writer(client)

    list_resp = await client.get("/writer", params={"agency_cnpj": agency["cnpj"]})
    assert list_resp.status_code == 200
    writers = list_resp.json() or []
    assert len(writers) == 1


async def test_route_get_writer_by_id(client):
    agency = await _create_writer(client)

    list_resp = await client.get("/writer", params={"agency_cnpj": agency["cnpj"]})
    assert list_resp.status_code == 200
    writers = list_resp.json() or []
    assert len(writers) == 1

    writer_id = writers[0]["id"]
    get_resp = await client.get(f"/writer/{writer_id}")
    assert get_resp.status_code == 200
    writer_data = get_resp.json()
    assert writer_data["id"] == writer_id
    assert writer_data["agency"]["id"] == agency["id"]
