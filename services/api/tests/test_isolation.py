import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_a_cannot_read_or_write_user_b_profile(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # User A sets their profile
    res_a = await client.put(
        "/v1/profile",
        json={"headline": "User A Headline", "status": "Engineer at Corp A"},
        headers=headers_a,
    )
    assert res_a.status_code == 200
    profile_a = res_a.json()
    assert profile_a["headline"] == "User A Headline"

    # User B gets their own profile - it should NOT be User A's profile
    res_b = await client.get("/v1/profile", headers=headers_b)
    assert res_b.status_code == 200
    profile_b = res_b.json()
    assert profile_b["id"] != profile_a["id"]
    assert profile_b["user_id"] != profile_a["user_id"]
    assert profile_b["headline"] is None


@pytest.mark.asyncio
async def test_user_a_cannot_read_modify_or_delete_user_b_facts(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # User B creates a fact
    create_res = await client.post(
        "/v1/facts",
        json={
            "kind": "experience",
            "title": "Secret Project B",
            "body": "Confidential details of User B",
            "tags": ["private", "work"],
            "confirmed": True,
        },
        headers=headers_b,
    )
    assert create_res.status_code == 201
    fact_b = create_res.json()
    fact_b_id = fact_b["id"]

    # 1. User A lists facts -> User B's fact must NOT appear
    list_res_a = await client.get("/v1/facts", headers=headers_a)
    assert list_res_a.status_code == 200
    facts_for_a = list_res_a.json()
    assert all(f["id"] != fact_b_id for f in facts_for_a)

    # 2. User A tries to PATCH User B's fact -> must return 404
    patch_res = await client.patch(
        f"/v1/facts/{fact_b_id}",
        json={"title": "Hacked Title"},
        headers=headers_a,
    )
    assert patch_res.status_code == 404
    assert patch_res.json()["detail"] == "Fact not found"

    # Verify fact was NOT modified
    list_res_b = await client.get("/v1/facts", headers=headers_b)
    assert list_res_b.status_code == 200
    b_facts = list_res_b.json()
    assert b_facts[0]["title"] == "Secret Project B"

    # 3. User A tries to DELETE User B's fact -> must return 404
    delete_res = await client.delete(f"/v1/facts/{fact_b_id}", headers=headers_a)
    assert delete_res.status_code == 404
    assert delete_res.json()["detail"] == "Fact not found"

    # Verify fact still exists for User B
    list_res_b_after = await client.get("/v1/facts", headers=headers_b)
    assert list_res_b_after.status_code == 200
    assert len(list_res_b_after.json()) == 1
