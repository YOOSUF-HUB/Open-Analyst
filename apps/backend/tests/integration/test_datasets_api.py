import io
import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.integration.conftest import make_csv, make_xlsx


def upload_csv(client: TestClient, content: str = "a,b\n1,2\n3,4\n") -> dict:
    data = make_csv(content)
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("test.csv", io.BytesIO(data), "text/csv")},
    )
    return response


def upload_xlsx(client: TestClient, sheet_data=None, filename="test.xlsx") -> dict:
    data = make_xlsx(sheet_data)
    response = client.post(
        "/api/v1/datasets/upload",
        files={
            "file": (
                filename,
                io.BytesIO(data),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    return response


# ---------------------------------------------------------------------------
# Upload CSV
# ---------------------------------------------------------------------------


def test_upload_csv_success(client):
    resp = upload_csv(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PROFILED"
    assert body["file_type"] == "csv"
    assert body["profile"] is not None
    assert body["profile"]["dataset"]["row_count"] == 2


def test_upload_csv_no_file(client):
    resp = client.post("/api/v1/datasets/upload")
    assert resp.status_code == 422


def test_upload_csv_unsupported_extension(client):
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("data.xls", io.BytesIO(b"a,b\n1,2\n"), "text/csv")},
    )
    assert resp.status_code == 400


def test_upload_empty_csv(client):
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert resp.status_code in (400, 413)


def test_upload_binary_as_csv_rejected(client):
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(bytes(range(256)) * 10), "text/csv")},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Upload Excel
# ---------------------------------------------------------------------------


def test_upload_xlsx_single_sheet_auto_profiled(client):
    resp = upload_xlsx(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "PROFILED"
    assert body["profile"] is not None


def test_upload_xlsx_multiple_sheets_needs_selection(client):
    sheet_data = {
        "Sales": [["month", "revenue"], ["Jan", 1000]],
        "Costs": [["month", "cost"], ["Jan", 500]],
    }
    resp = upload_xlsx(client, sheet_data=sheet_data)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "NEEDS_SHEET_SELECTION"
    assert len(body["sheet_names"]) == 2


def test_select_sheet(client):
    sheet_data = {
        "Alpha": [["x", "y"], [1, 2]],
        "Beta": [["p", "q"], [3, 4]],
    }
    upload_resp = upload_xlsx(client, sheet_data=sheet_data)
    dataset_id = upload_resp.json()["dataset_id"]

    profile_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/profile",
        json={"sheet_name": "Beta"},
    )
    assert profile_resp.status_code == 200
    body = profile_resp.json()
    assert body["status"] == "PROFILED"
    assert "p" in [c["name"] for c in body["profile"]["columns"]]


def test_select_invalid_sheet(client):
    sheet_data = {"Sheet1": [["a"], [1]]}
    upload_resp = upload_xlsx(client, sheet_data=sheet_data)
    dataset_id = upload_resp.json()["dataset_id"]

    # Even for single sheet, force profile endpoint
    resp = client.post(
        f"/api/v1/datasets/{dataset_id}/profile",
        json={"sheet_name": "DoesNotExist"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Get metadata / profile / preview
# ---------------------------------------------------------------------------


def test_get_dataset_metadata(client):
    resp = upload_csv(client)
    dataset_id = resp.json()["dataset_id"]

    get_resp = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["dataset_id"] == dataset_id
    assert body["status"] == "PROFILED"


def test_get_dataset_not_found(client):
    resp = client.get("/api/v1/datasets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_get_profile(client):
    resp = upload_csv(client)
    dataset_id = resp.json()["dataset_id"]

    profile_resp = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_resp.status_code == 200
    body = profile_resp.json()
    assert "dataset" in body
    assert "columns" in body
    assert "quality_warnings" in body


def test_get_preview(client):
    resp = upload_csv(client, "x,y\n" + "1,2\n" * 150)
    dataset_id = resp.json()["dataset_id"]

    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview?limit=50")
    assert preview_resp.status_code == 200
    body = preview_resp.json()
    assert body["preview_rows"] == 50
    assert body["total_rows"] == 150
    assert "x" in body["columns"]


def test_get_preview_default_limit(client):
    resp = upload_csv(client, "a,b\n" + "1,2\n" * 150)
    dataset_id = resp.json()["dataset_id"]

    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert preview_resp.status_code == 200
    assert preview_resp.json()["preview_rows"] == 100


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_dataset(client):
    resp = upload_csv(client)
    dataset_id = resp.json()["dataset_id"]

    del_resp = client.delete(f"/api/v1/datasets/{dataset_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "Dataset deleted."

    get_resp = client.get(f"/api/v1/datasets/{dataset_id}")
    assert get_resp.status_code == 404


def test_delete_nonexistent(client):
    resp = client.delete("/api/v1/datasets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Filename validation
# ---------------------------------------------------------------------------


def test_upload_long_filename_returns_400(client):
    long_name = "a" * 256 + ".csv"
    data = make_csv()
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": (long_name, io.BytesIO(data), "text/csv")},
    )
    assert resp.status_code == 400
    assert "too long" in resp.json()["detail"].lower()


# Null-byte filename: tested at unit level (validate_filename) because HTTP
# multipart encoding strips null bytes before they reach the application.

# ---------------------------------------------------------------------------
# Malformed CSV
# ---------------------------------------------------------------------------


def test_upload_malformed_csv_returns_422(client):
    malformed = b"col1,col2\n1,2\n3,4,extra_field\n"
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(malformed), "text/csv")},
    )
    assert resp.status_code == 422
    assert "parse" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Profile endpoint on non-XLSX dataset
# ---------------------------------------------------------------------------


def test_profile_csv_dataset_returns_400(client):
    resp = upload_csv(client)
    dataset_id = resp.json()["dataset_id"]

    profile_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/profile",
        json={"sheet_name": "Sheet1"},
    )
    assert profile_resp.status_code == 400
    assert "excel" in profile_resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Profile / preview on non-profiled datasets
# ---------------------------------------------------------------------------


def test_get_profile_not_profiled_returns_400(client):
    # Upload a multi-sheet XLSX → NEEDS_SHEET_SELECTION (not profiled)
    sheet_data = {
        "Alpha": [["x", "y"], [1, 2]],
        "Beta": [["p", "q"], [3, 4]],
    }
    resp = upload_xlsx(client, sheet_data=sheet_data)
    dataset_id = resp.json()["dataset_id"]
    assert resp.json()["status"] == "NEEDS_SHEET_SELECTION"

    profile_resp = client.get(f"/api/v1/datasets/{dataset_id}/profile")
    assert profile_resp.status_code == 400


def test_preview_needs_sheet_selection_returns_400(client):
    sheet_data = {
        "Alpha": [["x", "y"], [1, 2]],
        "Beta": [["p", "q"], [3, 4]],
    }
    resp = upload_xlsx(client, sheet_data=sheet_data)
    dataset_id = resp.json()["dataset_id"]

    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview")
    assert preview_resp.status_code == 400


# ---------------------------------------------------------------------------
# Storage cleanup after profiling failure
# ---------------------------------------------------------------------------


def test_file_cleaned_up_after_profiling_failure(client, tmp_upload_dir):
    # Malformed CSV passes content validators but fails read_csv (extra field)
    malformed = b"col1,col2\n1,2\n3,4,extra_field\n"
    resp = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("bad.csv", io.BytesIO(malformed), "text/csv")},
    )
    assert resp.status_code == 422
    # Storage directory must be empty — file was cleaned up
    remaining = list(tmp_upload_dir.iterdir())
    assert remaining == [], f"Expected no files after failure, found: {remaining}"


def test_storage_delete_failure_is_logged(client, caplog):
    resp = upload_csv(client)
    dataset_id = resp.json()["dataset_id"]

    with patch("app.api.v1.routes.datasets.get_storage") as mock_get_storage:
        mock_storage = mock_get_storage.return_value
        mock_storage.delete.side_effect = OSError("disk error")
        with caplog.at_level(logging.WARNING, logger="app.api.v1.routes.datasets"):
            del_resp = client.delete(f"/api/v1/datasets/{dataset_id}")

    assert del_resp.status_code == 200
    assert "Could not delete file" in caplog.text
