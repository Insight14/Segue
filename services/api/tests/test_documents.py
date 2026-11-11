from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_url_generation(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-doc-user"}
    with patch("api.services.s3.get_s3_client") as mock_s3:
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.local/fake-presigned-url"
        mock_s3.return_value = mock_client

        response = await client.post(
            "/v1/documents/upload-url",
            json={"filename": "resume.pdf", "mime": "application/pdf"},
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "document_id" in data
        assert data["upload_url"] == "https://s3.local/fake-presigned-url"
        assert "users/" in data["s3_key"]
        assert "resume.pdf" in data["s3_key"]


@pytest.mark.asyncio
async def test_upload_url_invalid_mime(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-doc-user"}
    response = await client.post(
        "/v1/documents/upload-url",
        json={"filename": "photo.png", "mime": "image/png"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_process_document(client: AsyncClient) -> None:
    headers = {"X-User-Sub": "test-doc-user-process"}
    with patch("api.services.s3.get_s3_client") as mock_s3:
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.local/url"
        mock_s3.return_value = mock_client

        create_res = await client.post(
            "/v1/documents/upload-url",
            json={"filename": "resume.pdf", "mime": "application/pdf"},
            headers=headers,
        )
        doc_id = create_res.json()["document_id"]

    with patch("api.services.queue.get_sqs_client") as mock_sqs:
        mock_sqs_client = MagicMock()
        mock_sqs.return_value = mock_sqs_client

        proc_res = await client.post(f"/v1/documents/{doc_id}/process", headers=headers)
        assert proc_res.status_code == 202
        assert proc_res.json()["status"] == "parsing"
        mock_sqs_client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_document_isolation(client: AsyncClient) -> None:
    headers_a = {"X-User-Sub": "user-doc-a"}
    headers_b = {"X-User-Sub": "user-doc-b"}

    with patch("api.services.s3.get_s3_client") as mock_s3:
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.local/url"
        mock_s3.return_value = mock_client

        create_res = await client.post(
            "/v1/documents/upload-url",
            json={"filename": "private_doc.pdf", "mime": "application/pdf"},
            headers=headers_a,
        )
        doc_a_id = create_res.json()["document_id"]

    # User B cannot get User A's document
    get_res_b = await client.get(f"/v1/documents/{doc_a_id}", headers=headers_b)
    assert get_res_b.status_code == 404

    # User B cannot process User A's document
    proc_res_b = await client.post(f"/v1/documents/{doc_a_id}/process", headers=headers_b)
    assert proc_res_b.status_code == 404

    # User B's list does not include User A's document
    list_res_b = await client.get("/v1/documents", headers=headers_b)
    assert list_res_b.status_code == 200
    assert all(d["id"] != doc_a_id for d in list_res_b.json())
