import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_threads(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-agent-user"}

    # 1. Create thread in Discover mode
    res = await client.post(
        "/v1/agent/threads",
        json={"mode": "discover", "title": "Career Exploration"},
        headers=headers,
    )
    assert res.status_code == 201
    thread = res.json()
    assert thread["mode"] == "discover"
    assert thread["title"] == "Career Exploration"
    assert len(thread["messages"]) == 1
    assert "project" in thread["messages"][0]["content"].lower()

    # 2. List threads
    list_res = await client.get("/v1/agent/threads", headers=headers)
    assert list_res.status_code == 200
    threads = list_res.json()
    assert len(threads) >= 1
    assert threads[0]["id"] == thread["id"]


@pytest.mark.asyncio
async def test_send_message_streaming_sse(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-agent-stream"}

    # Create thread
    res = await client.post(
        "/v1/agent/threads",
        json={"mode": "discover", "title": "Discovery Session"},
        headers=headers,
    )
    thread_id = res.json()["id"]

    # Send user message with SSE streaming
    stream_res = await client.post(
        f"/v1/agent/threads/{thread_id}/messages",
        json={
            "content": "I built an audio streaming server in Python using WebSockets and loved it."
        },
        headers=headers,
    )
    assert stream_res.status_code == 200
    assert "text/event-stream" in stream_res.headers["content-type"]
    body = stream_res.text
    assert "data: " in body
    assert "[DONE]" in body

    # Verify message was persisted in database
    get_res = await client.get(f"/v1/agent/threads/{thread_id}", headers=headers)
    assert get_res.status_code == 200
    thread_data = get_res.json()
    # Initial greeting + user message + assistant reply = 3 messages
    assert len(thread_data["messages"]) == 3
    assert thread_data["messages"][1]["role"] == "user"
    assert thread_data["messages"][2]["role"] == "assistant"


@pytest.mark.asyncio
async def test_talking_points_crud(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-tp-user"}

    # Add a confirmed fact
    await client.post(
        "/v1/facts",
        json={
            "kind": "experience",
            "title": "Built low latency streaming",
            "body": "Optimized audio buffers down to 20ms.",
            "tags": ["audio"],
            "source": "user",
            "confirmed": True,
        },
        headers=headers,
    )

    # Generate talking points
    gen_res = await client.post(
        "/v1/talking-points",
        json={"notes": "Meeting with wearable hardware lead"},
        headers=headers,
    )
    assert gen_res.status_code == 201
    tp = gen_res.json()
    assert "pitch_30s" in tp["content"]
    assert "questions_to_ask" in tp["content"]
    tp_id = tp["id"]

    # Retrieve by ID
    get_res = await client.get(f"/v1/talking-points/{tp_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == tp_id

    # List talking points
    list_res = await client.get("/v1/talking-points", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_agent_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "agent-user-a"}
    headers_b = {"X-User-Sub": "agent-user-b"}

    create_res = await client.post(
        "/v1/agent/threads",
        json={"mode": "prep", "title": "User A Private Thread"},
        headers=headers_a,
    )
    thread_a_id = create_res.json()["id"]

    # User B cannot get User A's thread
    get_b = await client.get(f"/v1/agent/threads/{thread_a_id}", headers=headers_b)
    assert get_b.status_code == 404

    # User B cannot message User A's thread
    msg_b = await client.post(
        f"/v1/agent/threads/{thread_a_id}/messages",
        json={"content": "Trying to snoop"},
        headers=headers_b,
    )
    assert msg_b.status_code == 404
