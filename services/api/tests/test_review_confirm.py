import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_review_and_confirm_endpoints(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-review-user"}

    # 1. Create an unconfirmed candidate fact (simulating resume extraction)
    create_res = await client.post(
        "/v1/facts",
        json={
            "kind": "experience",
            "title": "Proposed Fact from Resume",
            "body": "Lead architect on wearable streaming system.",
            "tags": ["resume", "wearables"],
            "source": "resume",
            "confirmed": False,  # Candidate state
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    fact_id = create_res.json()["id"]
    assert create_res.json()["confirmed"] is False

    # 2. Check the review queue endpoint: GET /v1/facts/review
    review_res = await client.get("/v1/facts/review", headers=headers)
    assert review_res.status_code == 200
    review_facts = review_res.json()
    assert len(review_facts) == 1
    assert review_facts[0]["id"] == fact_id
    assert review_facts[0]["confirmed"] is False

    # 3. Explicit user confirmation: POST /v1/facts/{id}/confirm
    confirm_res = await client.post(f"/v1/facts/{fact_id}/confirm", headers=headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["id"] == fact_id
    assert confirm_res.json()["confirmed"] is True

    # 4. Review queue is now empty
    review_res_after = await client.get("/v1/facts/review", headers=headers)
    assert review_res_after.status_code == 200
    assert len(review_res_after.json()) == 0

    # 5. Fact appears in confirmed list
    confirmed_res = await client.get("/v1/facts?confirmed=true", headers=headers)
    assert confirmed_res.status_code == 200
    assert any(f["id"] == fact_id for f in confirmed_res.json())
