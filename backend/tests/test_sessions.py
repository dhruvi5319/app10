"""Tests for session management endpoints."""

import pytest


def test_create_session_returns_201(client):
    """POST /api/sessions returns HTTP 201 with a session_id."""
    resp = client.post("/api/sessions")
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID v4 format


def test_get_session_returns_200(client, sample_session):
    """GET /api/sessions/{session_id} returns HTTP 200 for a valid session."""
    resp = client.get(f"/api/sessions/{sample_session}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == sample_session
    assert data["document_count"] == 0


def test_get_unknown_session_returns_404(client):
    """GET /api/sessions/{id} returns 404 for unknown session."""
    resp = client.get("/api/sessions/nonexistent-id-12345")
    assert resp.status_code == 404
    data = resp.json()
    assert data["detail"]["error_code"] == "SESSION_NOT_FOUND"


def test_two_sessions_are_distinct(client):
    """Two sequential POST /api/sessions return different session IDs."""
    r1 = client.post("/api/sessions")
    r2 = client.post("/api/sessions")
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["session_id"] != r2.json()["session_id"]
