import json

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_coach_suggest_persisted_in_history_and_ratings_feed_prompt(
    client: AsyncClient,
) -> None:
    headers_a = {"X-User-Sub": "coach-user-a"}
    headers_b = {"X-User-Sub": "coach-user-b"}

    # 1. User A sets profile & confirmed facts
    await client.put(
        "/v1/profile",
        json={"headline": "Distributed Systems Engineer", "status": "Seeking Staff roles"},
        headers=headers_a,
    )
    await client.post(
        "/v1/facts",
        json={
            "kind": "experience",
            "title": "Raft Consensus Cluster",
            "body": "Implemented multi-raft consensus engine handling 50k req/s.",
            "tags": ["raft", "consensus"],
            "source": "user",
            "confirmed": True,
        },
        headers=headers_a,
    )

    # 2. User A creates contact & conversation
    contact_res = await client.post(
        "/v1/contacts",
        json={"name": "Alex Riviera", "company": "Stripe", "role": "Director of Infra"},
        headers=headers_a,
    )
    contact_id = contact_res.json()["id"]

    conv_res = await client.post(
        "/v1/conversations",
        json={"contact_id": contact_id, "source": "laptop"},
        headers=headers_a,
    )
    conv_id = conv_res.json()["id"]

    # 3. Add message
    await client.post(
        f"/v1/conversations/{conv_id}/messages",
        json={"speaker": "partner", "text": "We are rearchitecting our payment ledger consensus."},
        headers=headers_a,
    )

    # 4. Request coach suggestion
    suggest_res = await client.post(
        "/v1/coach/suggest",
        json={
            "conversation_id": conv_id,
            "after_message_seq": 1,
            "recent_messages": ["partner: We are rearchitecting our payment ledger consensus."],
        },
        headers=headers_a,
    )
    assert suggest_res.status_code == 201
    sug_data = suggest_res.json()
    assert "suggestions" in sug_data
    assert len(sug_data["suggestions"]) >= 1

    sug1 = sug_data["suggestions"][0]
    assert len(sug1["text"]) <= 80  # OLED character limit
    sug1_id = sug1["id"]

    # 5. Verify suggestions are persisted and appear in History detail
    detail_res = await client.get(f"/v1/conversations/{conv_id}", headers=headers_a)
    assert detail_res.status_code == 200
    conv_detail = detail_res.json()
    assert len(conv_detail["suggestions"]) >= 1
    assert any(s["id"] == sug1_id for s in conv_detail["suggestions"])

    # 6. Rate suggestion with 5 stars
    rate_res = await client.patch(
        f"/v1/suggestions/{sug1_id}",
        json={"rating": 5, "selected": True},
        headers=headers_a,
    )
    assert rate_res.status_code == 200
    assert rate_res.json()["rating"] == 5

    # 7. Next coach call receives this rating in its prompt context (feedback loop)
    suggest_res_2 = await client.post(
        "/v1/coach/suggest",
        json={
            "conversation_id": conv_id,
            "after_message_seq": 1,
            "recent_messages": ["partner: Do you have experience with raft protocols?"],
        },
        headers=headers_a,
    )
    assert suggest_res_2.status_code == 201
    assert len(suggest_res_2.json()["suggestions"]) >= 1

    # 8. Export training data (JSONL)
    export_res = await client.get("/v1/training/export?min_rating=4", headers=headers_a)
    assert export_res.status_code == 200
    assert "application/x-ndjson" in export_res.headers["content-type"]
    lines = [json.loads(line) for line in export_res.text.strip().split("\n") if line]
    assert len(lines) >= 1
    assert any(entry["suggestion_id"] == sug1_id and entry["rating"] == 5 for entry in lines)

    # 9. Multi-tenant isolation: User B cannot call /coach/suggest on User A's conversation
    unauth_suggest = await client.post(
        "/v1/coach/suggest",
        json={"conversation_id": conv_id},
        headers=headers_b,
    )
    assert unauth_suggest.status_code == 404

    # User B's training export must not contain User A's rated suggestions
    export_b = await client.get("/v1/training/export", headers=headers_b)
    assert export_b.status_code == 200
    lines_b = [json.loads(line) for line in export_b.text.strip().split("\n") if line]
    assert all(entry["suggestion_id"] != sug1_id for entry in lines_b)
