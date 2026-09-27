import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db


def test_document_upload_download_and_rejection(admin_client, active_policy, media_root, settings):
    upload = SimpleUploadedFile("schedule.pdf", b"%PDF-1.1\nhello", content_type="application/pdf")
    created = admin_client.post(
        "/api/documents/",
        {"name": "Health schedule", "type": "policy", "policy": active_policy.id, "file": upload},
        format="multipart",
    )
    assert created.status_code == 201
    assert created.data["size"] == len(b"%PDF-1.1\nhello")
    assert created.data["url"]
    document_id = created.data["id"]

    downloaded = admin_client.get(f"/api/documents/{document_id}/download/")
    assert downloaded.status_code == 200
    body = b"".join(downloaded.streaming_content)
    assert body.startswith(b"%PDF-1.1")

    missing_link = admin_client.post(
        "/api/documents/",
        {
            "name": "Loose file",
            "type": "policy",
            "file": SimpleUploadedFile("loose.pdf", b"%PDF-1.1", content_type="application/pdf"),
        },
        format="multipart",
    )
    assert missing_link.status_code == 400

    bad_type = admin_client.post(
        "/api/documents/",
        {
            "name": "Script",
            "type": "other",
            "file": SimpleUploadedFile("run.exe", b"MZ", content_type="application/octet-stream"),
        },
        format="multipart",
    )
    assert bad_type.status_code == 400

    settings.MAX_UPLOAD_BYTES = 8
    too_big = admin_client.post(
        "/api/documents/",
        {
            "name": "Big",
            "type": "policy",
            "policy": active_policy.id,
            "file": SimpleUploadedFile("big.pdf", b"0123456789", content_type="application/pdf"),
        },
        format="multipart",
    )
    assert too_big.status_code == 400


def test_identity_mock_outcomes(underwriter_client, customer):
    verified = underwriter_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "passport", "document_number": "p1234567"},
        format="json",
    )
    assert verified.status_code == 201
    assert verified.data["status"] == "verified"
    assert verified.data["provider"] == "mock"
    assert verified.data["document_number"] == "P1234567"

    rejected = underwriter_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "passport", "document_number": "P1234567X"},
        format="json",
    )
    assert rejected.status_code == 201
    assert rejected.data["status"] == "failed"

    short = underwriter_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "national_id", "document_number": "A12"},
        format="json",
    )
    assert short.data["status"] == "failed"

    review = underwriter_client.post(
        "/api/identity/verify/",
        {"customer": customer.id, "document_type": "drivers_license", "document_number": "DL998877"},
        format="json",
    )
    assert review.data["status"] == "manual_review"

    history = underwriter_client.get(f"/api/identity/verifications/?customer={customer.id}")
    assert history.status_code == 200
    assert history.data["count"] == 4
