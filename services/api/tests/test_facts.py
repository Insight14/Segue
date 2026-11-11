import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_crud_facts(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-user-facts"}

    # 1. Create a fact
    create_payload = {
        "kind": "experience",
        "title": "Built real-time speech coach",
        "body": "Integrated Whisper and Ollama with Grove OLED display over serial.",
        "tags": ["hardware", "llm", "python"],
        "source": "user",
        "confirmed": True,
    }
    create_res = await client.post("/v1/facts", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    fact = create_res.json()
    assert fact["title"] == create_payload["title"]
    assert fact["kind"] == "experience"
    assert fact["tags"] == ["hardware", "llm", "python"]
    assert fact["confirmed"] is True
    fact_id = fact["id"]

    # 2. List facts
    list_res = await client.get("/v1/facts", headers=headers)
    assert list_res.status_code == 200
    facts_list = list_res.json()
    assert len(facts_list) == 1
    assert facts_list[0]["id"] == fact_id

    # 3. Patch fact
    patch_payload = {
        "kind": "skill",
        "title": "Built real-time smart-glasses coach",
        "confirmed": False,
        "tags": ["wearables", "iot"],
    }
    patch_res = await client.patch(f"/v1/facts/{fact_id}", json=patch_payload, headers=headers)
    assert patch_res.status_code == 200
    updated_fact = patch_res.json()
    assert updated_fact["title"] == "Built real-time smart-glasses coach"
    assert updated_fact["kind"] == "skill"
    assert updated_fact["confirmed"] is False
    assert updated_fact["tags"] == ["wearables", "iot"]

    # 4. Delete fact
    del_res = await client.delete(f"/v1/facts/{fact_id}", headers=headers)
    assert del_res.status_code == 204

    # 5. Verify deletion
    list_res_empty = await client.get("/v1/facts", headers=headers)
    assert list_res_empty.status_code == 200
    assert len(list_res_empty.json()) == 0


@pytest.mark.asyncio
async def test_fact_filters(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-filter-user"}

    # Add three facts with distinct kinds, confirmation, and tags
    await client.post(
        "/v1/facts",
        json={
            "kind": "education",
            "title": "B.S. CS",
            "body": "University",
            "tags": ["school"],
            "confirmed": True,
        },
        headers=headers,
    )
    await client.post(
        "/v1/facts",
        json={
            "kind": "skill",
            "title": "Python & FastAPI",
            "body": "Backend",
            "tags": ["code"],
            "confirmed": True,
        },
        headers=headers,
    )
    await client.post(
        "/v1/facts",
        json={
            "kind": "skill",
            "title": "Rust",
            "body": "Systems",
            "tags": ["code"],
            "confirmed": False,
        },
        headers=headers,
    )

    # Filter by kind
    res_kind = await client.get("/v1/facts?kind=skill", headers=headers)
    assert res_kind.status_code == 200
    assert len(res_kind.json()) == 2

    # Filter by confirmed
    res_confirmed = await client.get("/v1/facts?confirmed=true", headers=headers)
    assert res_confirmed.status_code == 200
    assert len(res_confirmed.json()) == 2

    # Filter by tag
    res_tag = await client.get("/v1/facts?tag=school", headers=headers)
    assert res_tag.status_code == 200
    assert len(res_tag.json()) == 1
    assert res_tag.json()[0]["kind"] == "education"


@pytest.mark.asyncio
async def test_fact_not_found_and_validation(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-validation-user"}
    random_id = uuid.uuid4()

    # 404 on nonexistent fact
    res_404_patch = await client.patch(
        f"/v1/facts/{random_id}", json={"title": "new"}, headers=headers
    )
    assert res_404_patch.status_code == 404

    res_404_del = await client.delete(f"/v1/facts/{random_id}", headers=headers)
    assert res_404_del.status_code == 404

    # 422 on invalid kind
    res_invalid = await client.post(
        "/v1/facts",
        json={"kind": "invalid_kind_123", "title": "Bad", "body": "Body"},
        headers=headers,
    )
    assert res_invalid.status_code == 422
