import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_events_crud_and_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # 1. User A creates an event
    create_res = await client.post(
        "/v1/events",
        json={
            "name": "KubeCon 2026",
            "type": "Conference",
            "notes": "Networking with platform engineers",
        },
        headers=headers_a,
    )
    assert create_res.status_code == 201
    event_a = create_res.json()
    event_id = event_a["id"]
    assert event_a["name"] == "KubeCon 2026"

    # 2. User A gets the event
    get_res = await client.get(f"/v1/events/{event_id}", headers=headers_a)
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "KubeCon 2026"

    # 3. User B cannot see or get User A's event
    list_b = await client.get("/v1/events", headers=headers_b)
    assert list_b.status_code == 200
    assert all(e["id"] != event_id for e in list_b.json())

    get_b = await client.get(f"/v1/events/{event_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 4. User A updates the event
    patch_res = await client.patch(
        f"/v1/events/{event_id}",
        json={"notes": "Updated notes"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["notes"] == "Updated notes"

    # 5. User B cannot delete User A's event
    del_b = await client.delete(f"/v1/events/{event_id}", headers=headers_b)
    assert del_b.status_code == 404

    # 6. User A deletes the event
    del_a = await client.delete(f"/v1/events/{event_id}", headers=headers_a)
    assert del_a.status_code == 204

    # Confirm 404 after deletion
    get_deleted = await client.get(f"/v1/events/{event_id}", headers=headers_a)
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_contacts_crud_and_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # 1. User A creates a contact
    create_res = await client.post(
        "/v1/contacts",
        json={
            "name": "Jordan Lee",
            "company": "Datadog",
            "role": "Staff SRE",
            "notes": "Discussed eBPF tooling",
            "consent_noted": True,
        },
        headers=headers_a,
    )
    assert create_res.status_code == 201
    contact_a = create_res.json()
    contact_id = contact_a["id"]
    assert contact_a["name"] == "Jordan Lee"
    assert contact_a["consent_noted"] is True

    # 2. User B cannot see or get User A's contact
    list_b = await client.get("/v1/contacts", headers=headers_b)
    assert list_b.status_code == 200
    assert all(c["id"] != contact_id for c in list_b.json())

    get_b = await client.get(f"/v1/contacts/{contact_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 3. User A updates contact
    patch_res = await client.patch(
        f"/v1/contacts/{contact_id}",
        json={"role": "Principal SRE"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["role"] == "Principal SRE"

    # 4. User A deletes contact
    del_res = await client.delete(f"/v1/contacts/{contact_id}", headers=headers_a)
    assert del_res.status_code == 204

    # Confirm 404
    get_del = await client.get(f"/v1/contacts/{contact_id}", headers=headers_a)
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_conversation_lifecycle_cascade_and_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # 1. Create Event and Contact for User A
    event_res = await client.post(
        "/v1/events",
        json={"name": "AI Meetup"},
        headers=headers_a,
    )
    event_id = event_res.json()["id"]

    contact_res = await client.post(
        "/v1/contacts",
        json={"name": "Sam Taylor", "company": "Anthropic", "event_id": event_id},
        headers=headers_a,
    )
    contact_id = contact_res.json()["id"]

    # 2. Create conversation
    conv_res = await client.post(
        "/v1/conversations",
        json={
            "contact_id": contact_id,
            "event_id": event_id,
            "source": "phone",
        },
        headers=headers_a,
    )
    assert conv_res.status_code == 201
    conv = conv_res.json()
    conv_id = conv["id"]

    # 3. Add Messages
    m1_res = await client.post(
        f"/v1/conversations/{conv_id}/messages",
        json={"speaker": "partner", "text": "What do you think of modern LLM eval frameworks?"},
        headers=headers_a,
    )
    assert m1_res.status_code == 201
    assert m1_res.json()["seq"] == 1

    m2_res = await client.post(
        f"/v1/conversations/{conv_id}/messages",
        json={"speaker": "user", "text": "I think deterministic regression test sets are crucial."},
        headers=headers_a,
    )
    assert m2_res.status_code == 201
    assert m2_res.json()["seq"] == 2

    # 4. Search and filter conversations
    search_res = await client.get("/v1/conversations?q=deterministic", headers=headers_a)
    assert search_res.status_code == 200
    assert any(c["id"] == conv_id for c in search_res.json())

    # 5. User B cannot see conversation
    list_b = await client.get("/v1/conversations", headers=headers_b)
    assert all(c["id"] != conv_id for c in list_b.json())

    detail_b = await client.get(f"/v1/conversations/{conv_id}", headers=headers_b)
    assert detail_b.status_code == 404

    # 6. User A gets detail
    detail_a = await client.get(f"/v1/conversations/{conv_id}", headers=headers_a)
    assert detail_a.status_code == 200
    data_a = detail_a.json()
    assert len(data_a["messages"]) == 2
    assert data_a["contact"]["name"] == "Sam Taylor"
    assert data_a["event"]["name"] == "AI Meetup"

    # 7. Update conversation summary
    patch_res = await client.patch(
        f"/v1/conversations/{conv_id}",
        json={"summary": "Productive conversation about eval methodologies"},
        headers=headers_a,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["summary"] == "Productive conversation about eval methodologies"

    # 8. Export as JSON
    export_json = await client.get(
        f"/v1/conversations/{conv_id}/export?format=json", headers=headers_a
    )
    assert export_json.status_code == 200
    assert "application/json" in export_json.headers["content-type"]
    exported_data = export_json.json()
    assert exported_data["conversation"]["id"] == conv_id
    assert len(exported_data["messages"]) == 2

    # 9. Export as text
    export_txt = await client.get(
        f"/v1/conversations/{conv_id}/export?format=text", headers=headers_a
    )
    assert export_txt.status_code == 200
    assert "text/plain" in export_txt.headers["content-type"]
    assert "deterministic" in export_txt.text

    # 10. Delete conversation (hard delete)
    del_res = await client.delete(f"/v1/conversations/{conv_id}", headers=headers_a)
    assert del_res.status_code == 204

    # Verify hard deletion
    get_del = await client.get(f"/v1/conversations/{conv_id}", headers=headers_a)
    assert get_del.status_code == 404


@pytest.mark.asyncio
async def test_suggestion_rating_and_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-a", "X-User-Email": "a@example.com"}
    headers_b = {"X-User-Sub": "user-b", "X-User-Email": "b@example.com"}

    # Create conversation for User A
    conv_res = await client.post(
        "/v1/conversations",
        json={"source": "laptop"},
        headers=headers_a,
    )
    conv_id = conv_res.json()["id"]

    # Insert suggestion directly using db session or via direct route
    from api.db import get_db
    from api.main import app
    from api.models.conversation import Suggestion

    override_db = app.dependency_overrides[get_db]
    async for session in override_db():
        sug = Suggestion(
            conversation_id=uuid.UUID(conv_id),
            after_message_seq=1,
            text="Mention your experience with distributed consensus",
            shown=True,
            selected=True,
        )
        session.add(sug)
        await session.commit()
        await session.refresh(sug)
        sug_id = str(sug.id)
        break

    # User B cannot update User A's suggestion
    patch_b = await client.patch(
        f"/v1/suggestions/{sug_id}",
        json={"rating": 1},
        headers=headers_b,
    )
    assert patch_b.status_code == 404

    # User A rates the suggestion 5 stars
    patch_a = await client.patch(
        f"/v1/suggestions/{sug_id}",
        json={"rating": 5},
        headers=headers_a,
    )
    assert patch_a.status_code == 200
    assert patch_a.json()["rating"] == 5
    assert patch_a.json()["shown"] is True
