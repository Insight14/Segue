import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_profile_auto_creation(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-user-profile"}
    response = await client.get("/v1/profile", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert data["headline"] is None


@pytest.mark.asyncio
async def test_put_profile_update(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-user-profile-2"}
    update_data = {
        "headline": "Junior Software Engineer",
        "status": "CS Junior looking for summer 2027 internships",
        "goals": "Break into distributed systems and wearable AI",
        "tone_preference": "approachable, thoughtful",
        "summary_md": "## About Me\nPassionate about low-latency systems.",
    }
    response = await client.put("/v1/profile", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["headline"] == update_data["headline"]
    assert data["status"] == update_data["status"]
    assert data["goals"] == update_data["goals"]
    assert data["tone_preference"] == update_data["tone_preference"]
    assert data["summary_md"] == update_data["summary_md"]

    # Verify GET returns updated data
    get_res = await client.get("/v1/profile", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["headline"] == update_data["headline"]
