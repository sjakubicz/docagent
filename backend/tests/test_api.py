from pathlib import Path

from fastapi.testclient import TestClient


def upload(client: TestClient, path: Path) -> dict:
    with path.open("rb") as f:
        response = client.post("/api/documents", files={"file": (path.name, f, "application/pdf")})
    assert response.status_code == 202
    return response.json()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_processes_pdf_in_background(client, sample_pdf):
    created = upload(client, sample_pdf)
    assert created["status"] == "processing"

    (doc,) = client.get("/api/documents").json()
    assert doc["id"] == created["id"]
    assert doc["status"] == "ready"
    assert doc["num_pages"] == 2
    assert doc["ocr_pages"] == 0


def test_scanned_pdf_is_marked_as_ocr(client, scanned_pdf):
    upload(client, scanned_pdf)
    (doc,) = client.get("/api/documents").json()
    assert doc["ocr_pages"] == 1


def test_broken_pdf_is_marked_failed(client):
    response = client.post(
        "/api/documents", files={"file": ("broken.pdf", b"not a pdf", "application/pdf")}
    )
    assert response.status_code == 202
    (doc,) = client.get("/api/documents").json()
    assert doc["status"] == "failed"
    assert doc["error"]


def test_rejects_non_pdf(client):
    response = client.post("/api/documents", files={"file": ("notes.txt", b"hi", "text/plain")})
    assert response.status_code == 400


def test_delete_document(client, sample_pdf):
    doc = upload(client, sample_pdf)
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
    assert client.post("/api/search", json={"query": "lisinopril"}).json() == []


def test_delete_missing_document_returns_404(client):
    assert client.delete("/api/documents/999").status_code == 404


def test_search_finds_uploaded_text(client, sample_pdf):
    upload(client, sample_pdf)
    for mode in ("bm25", "vector", "hybrid"):
        hits = client.post(
            "/api/search", json={"query": "lisinopril dry cough", "mode": mode, "k": 3}
        ).json()
        assert hits[0]["filename"] == sample_pdf.name
        assert hits[0]["page"] == 1


def test_search_validates_input(client):
    assert client.post("/api/search", json={"query": ""}).status_code == 422
    assert client.post("/api/search", json={"query": "x", "k": 0}).status_code == 422


def test_document_deleted_before_processing_is_skipped(db, sample_pdf):
    from docagent.db import Document
    from docagent.ingest.pipeline import create_document, process_document

    doc = create_document(db, sample_pdf.name, sample_pdf.read_bytes())
    db.delete(doc)
    db.commit()
    process_document(doc.id, sample_pdf.read_bytes())
    assert db.get(Document, doc.id) is None


def test_document_detail_lists_pages_with_ocr_flag(client, scanned_pdf):
    doc = upload(client, scanned_pdf)
    detail = client.get(f"/api/documents/{doc['id']}").json()
    assert detail["has_file"] is True
    (page,) = detail["pages"]
    assert page["number"] == 1
    assert page["ocr"] is True
    assert "paracetamol" in page["text"].lower()


def test_document_file_returns_original_pdf(client, sample_pdf):
    doc = upload(client, sample_pdf)
    response = client.get(f"/api/documents/{doc['id']}/file")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == sample_pdf.read_bytes()


def test_document_without_stored_file(client, db, sample_pdf):
    from docagent.db import Document

    doc = upload(client, sample_pdf)
    stored = db.get_one(Document, doc["id"])
    stored.content = None
    db.commit()
    assert client.get(f"/api/documents/{doc['id']}").json()["has_file"] is False
    assert client.get(f"/api/documents/{doc['id']}/file").status_code == 404


def test_missing_document_detail_returns_404(client):
    assert client.get("/api/documents/999").status_code == 404
