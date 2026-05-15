"""Tests for document upload, status, list, and delete endpoints."""

import io
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_upload_txt_returns_202(client, sample_session, mock_openai_embeddings):
    """Upload a TXT file returns HTTP 202 immediately."""
    txt_content = (FIXTURES_DIR / "sample.txt").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("sample.txt", io.BytesIO(txt_content), "text/plain")},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["session_id"] == sample_session
    assert data["filename"] == "sample.txt"
    assert data["status"] == "UPLOADING"
    assert "doc_id" in data


def test_upload_pdf_returns_202(client, sample_session, mock_openai_embeddings):
    """Upload a PDF file returns HTTP 202."""
    pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 202
    assert resp.json()["filename"] == "sample.pdf"


def test_upload_docx_returns_202(client, sample_session, mock_openai_embeddings):
    """Upload a DOCX file returns HTTP 202."""
    docx_bytes = (FIXTURES_DIR / "sample.docx").read_bytes()
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={
            "file": (
                "sample.docx",
                io.BytesIO(docx_bytes),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert resp.status_code == 202
    assert resp.json()["filename"] == "sample.docx"


def test_upload_too_large_returns_413(client, sample_session):
    """Upload a file exceeding MAX_FILE_SIZE_MB returns HTTP 413."""
    # 21 MB of zeros
    big_file = b"\x00" * (21 * 1024 * 1024)
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("big.txt", io.BytesIO(big_file), "text/plain")},
    )
    assert resp.status_code == 413
    assert resp.json()["detail"]["error_code"] == "FILE_TOO_LARGE"


def test_upload_wrong_type_returns_422(client, sample_session):
    """Upload a JPEG (non-document) returns HTTP 422 INVALID_MIME_TYPE."""
    # Minimal JPEG magic bytes
    jpeg_bytes = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"\x00" * 100
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("image.jpg", io.BytesIO(jpeg_bytes), "image/jpeg")},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error_code"] == "INVALID_MIME_TYPE"


def test_upload_unknown_session_returns_404(client):
    """Upload to a nonexistent session returns HTTP 404."""
    txt = b"hello world"
    resp = client.post(
        "/api/documents/upload",
        data={"session_id": "nonexistent-session"},
        files={"file": ("test.txt", io.BytesIO(txt), "text/plain")},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "SESSION_NOT_FOUND"


def test_get_document_status(client, sample_session, mock_openai_embeddings):
    """GET /api/documents/{doc_id}/status returns document details."""
    txt_content = (FIXTURES_DIR / "sample.txt").read_bytes()
    upload_resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("sample.txt", io.BytesIO(txt_content), "text/plain")},
    )
    doc_id = upload_resp.json()["doc_id"]

    status_resp = client.get(f"/api/documents/{doc_id}/status")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["doc_id"] == doc_id
    assert data["session_id"] == sample_session
    assert data["filename"] == "sample.txt"
    assert data["status"] in ("UPLOADING", "PARSING", "CHUNKING", "EMBEDDING", "INDEXING", "READY", "FAILED")


def test_list_documents(client, sample_session, mock_openai_embeddings):
    """GET /api/documents?session_id=... returns document list."""
    txt = (FIXTURES_DIR / "sample.txt").read_bytes()
    client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("sample.txt", io.BytesIO(txt), "text/plain")},
    )

    resp = client.get(f"/api/documents?session_id={sample_session}")
    assert resp.status_code == 200
    docs = resp.json()["documents"]
    assert len(docs) >= 1
    assert docs[0]["session_id"] == sample_session


def test_delete_document(client, sample_session, mock_openai_embeddings):
    """DELETE /api/documents/{doc_id} returns 204 and removes the document."""
    txt = (FIXTURES_DIR / "sample.txt").read_bytes()
    upload_resp = client.post(
        "/api/documents/upload",
        data={"session_id": sample_session},
        files={"file": ("sample.txt", io.BytesIO(txt), "text/plain")},
    )
    doc_id = upload_resp.json()["doc_id"]

    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204

    status_resp = client.get(f"/api/documents/{doc_id}/status")
    assert status_resp.status_code == 404
