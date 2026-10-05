from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models.address import Address

MANILA = {
    "name": "Maria Dela Cruz",
    "birthday": "1990-05-15",
    "home_number": "+63-2-8123-4567",
    "cellphone_number": "+63-917-123-4567",
    "email": "maria@example.com",
    "notes": "Prefers calls after 6 PM.",
    "street": "Rizal Park",
    "city": "Manila",
    "state": "Metro Manila",
    "postal_code": "1000",
    "country": "Philippines",
    "latitude": 14.5995,
    "longitude": 120.9842,
}

QUEZON_CITY = {
    "name": "Jose Santos",
    "birthday": "1988-11-02",
    "home_number": "+63-2-8123-7654",
    "cellphone_number": "+63-921-765-4321",
    "email": "jose@example.com",
    "notes": "Works in the city hall.",
    "street": "Quezon Memorial Circle",
    "city": "Quezon City",
    "state": "Metro Manila",
    "postal_code": "1100",
    "country": "Philippines",
    "latitude": 14.6511,
    "longitude": 121.0493,
}

TOKYO = {
    "name": "Akira Tanaka",
    "birthday": "1985-08-20",
    "home_number": "+81-3-1234-5678",
    "cellphone_number": "+81-90-1234-5678",
    "email": "akira@example.com",
    "notes": "Travels often for business.",
    "street": "1 Chome-1-2 Oshiage",
    "city": "Tokyo",
    "state": "Tokyo",
    "postal_code": "131-0045",
    "country": "Japan",
    "latitude": 35.7101,
    "longitude": 139.8107,
}


def test_create_and_get_address(client: TestClient) -> None:
    created = client.post("/api/v1/addresses", json=MANILA)
    assert created.status_code == 201
    address_id = created.json()["id"]

    fetched = client.get(f"/api/v1/addresses/{address_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == MANILA["name"]
    assert fetched.json()["birthday"] == MANILA["birthday"]
    assert fetched.json()["email"] == MANILA["email"]
    assert fetched.json()["home_number"] == MANILA["home_number"]
    assert fetched.json()["cellphone_number"] == MANILA["cellphone_number"]
    assert fetched.json()["notes"] == MANILA["notes"]
    assert fetched.json()["city"] == "Manila"
    assert fetched.json()["latitude"] == MANILA["latitude"]


def test_create_rejects_invalid_coordinates(client: TestClient) -> None:
    payload = {**MANILA, "latitude": 100}
    response = client.post("/api/v1/addresses", json=payload)
    assert response.status_code == 422


def test_create_rejects_missing_required_fields_and_invalid_email(client: TestClient) -> None:
    missing_name = {key: value for key, value in MANILA.items() if key != "name"}
    invalid_email = {**MANILA, "email": "not-an-email"}

    assert client.post("/api/v1/addresses", json=missing_name).status_code == 422
    assert client.post("/api/v1/addresses", json=invalid_email).status_code == 422


def test_email_must_be_unique_for_active_addresses(client: TestClient) -> None:
    first = client.post("/api/v1/addresses", json=MANILA)
    duplicate = client.post(
        "/api/v1/addresses",
        json={**QUEZON_CITY, "email": MANILA["email"].upper()},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_update_and_delete_address(client: TestClient) -> None:
    created = client.post("/api/v1/addresses", json=MANILA)
    address_id = created.json()["id"]

    updated = client.patch(f"/api/v1/addresses/{address_id}", json={"city": "Makati"})
    assert updated.status_code == 200
    assert updated.json()["city"] == "Makati"

    deleted = client.delete(f"/api/v1/addresses/{address_id}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/v1/addresses/{address_id}")
    assert missing.status_code == 404


def test_update_rejects_duplicate_email_without_changing_address(client: TestClient) -> None:
    client.post("/api/v1/addresses", json=MANILA)
    second = client.post("/api/v1/addresses", json=QUEZON_CITY).json()

    conflict = client.patch(
        f"/api/v1/addresses/{second['id']}",
        json={"email": MANILA["email"]},
    )
    unchanged = client.get(f"/api/v1/addresses/{second['id']}")

    assert conflict.status_code == 409
    assert unchanged.status_code == 200
    assert unchanged.json()["email"] == QUEZON_CITY["email"]


def test_update_normalizes_email_and_returns_saved_fields(client: TestClient) -> None:
    address_id = client.post("/api/v1/addresses", json=MANILA).json()["id"]

    response = client.patch(
        f"/api/v1/addresses/{address_id}",
        json={"email": "MARIA.NEW@EXAMPLE.COM", "notes": "Updated note"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "maria.new@example.com"
    assert response.json()["notes"] == "Updated note"


def test_update_rejects_null_for_required_field_but_accepts_nullable_notes(
    client: TestClient,
) -> None:
    address_id = client.post("/api/v1/addresses", json=MANILA).json()["id"]

    invalid = client.patch(f"/api/v1/addresses/{address_id}", json={"name": None})
    valid = client.patch(f"/api/v1/addresses/{address_id}", json={"notes": None})

    assert invalid.status_code == 422
    assert valid.status_code == 200
    assert valid.json()["notes"] is None


def test_deleted_address_email_can_be_reused(
    client: TestClient,
    test_engine: Engine,
) -> None:
    created = client.post("/api/v1/addresses", json=MANILA)
    address_id = created.json()["id"]
    deleted = client.delete(f"/api/v1/addresses/{address_id}")
    recreated = client.post("/api/v1/addresses", json=MANILA)
    listed = client.get("/api/v1/addresses")

    assert deleted.status_code == 204
    assert recreated.status_code == 201
    assert recreated.json()["email"] == MANILA["email"]
    assert [item["id"] for item in listed.json()["items"]] == [recreated.json()["id"]]
    assert client.get(f"/api/v1/addresses/{address_id}").status_code == 404
    with Session(test_engine) as db:
        deleted_address = db.get(Address, address_id)
        assert deleted_address is not None
        assert deleted_address.deleted_at is not None
        assert deleted_address.email.endswith("@deleted.invalid")


def test_nearby_search_filters_by_distance(client: TestClient) -> None:
    client.post("/api/v1/addresses", json=MANILA)
    client.post("/api/v1/addresses", json=QUEZON_CITY)
    client.post("/api/v1/addresses", json=TOKYO)

    nearby = client.get(
        "/api/v1/addresses/nearby",
        params={
            "latitude": MANILA["latitude"],
            "longitude": MANILA["longitude"],
            "distance_km": 15,
        },
    )
    assert nearby.status_code == 200
    cities = {item["city"] for item in nearby.json()["items"]}
    assert cities == {"Manila", "Quezon City"}
    assert nearby.json()["pagination"] == {
        "total": 2,
        "limit": 20,
        "offset": 0,
        "has_more": False,
    }


def test_list_addresses_supports_limit_and_offset(client: TestClient) -> None:
    client.post("/api/v1/addresses", json=MANILA)
    client.post("/api/v1/addresses", json=QUEZON_CITY)
    client.post("/api/v1/addresses", json=TOKYO)

    response = client.get("/api/v1/addresses", params={"limit": 1, "offset": 1})

    assert response.status_code == 200
    assert [item["city"] for item in response.json()["items"]] == ["Quezon City"]
    assert response.json()["pagination"] == {
        "total": 3,
        "limit": 1,
        "offset": 1,
        "has_more": True,
    }


def test_nearby_search_paginates_matching_addresses(client: TestClient) -> None:
    client.post("/api/v1/addresses", json=TOKYO)
    client.post("/api/v1/addresses", json=MANILA)
    client.post("/api/v1/addresses", json=QUEZON_CITY)

    response = client.get(
        "/api/v1/addresses/nearby",
        params={
            "latitude": MANILA["latitude"],
            "longitude": MANILA["longitude"],
            "distance_km": 15,
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200
    assert [item["city"] for item in response.json()["items"]] == ["Quezon City"]
    assert response.json()["pagination"] == {
        "total": 2,
        "limit": 1,
        "offset": 1,
        "has_more": False,
    }


def test_list_addresses_returns_empty_page_and_correct_total_for_large_offset(
    client: TestClient,
) -> None:
    client.post("/api/v1/addresses", json=MANILA)
    response = client.get("/api/v1/addresses", params={"limit": 10, "offset": 10})

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["pagination"] == {
        "total": 1,
        "limit": 10,
        "offset": 10,
        "has_more": False,
    }


def test_pagination_validation_applies_to_both_collection_endpoints(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/addresses", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/addresses", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/addresses", params={"offset": -1}).status_code == 422

    nearby_url = "/api/v1/addresses/nearby"
    base_params = {
        "latitude": MANILA["latitude"],
        "longitude": MANILA["longitude"],
        "distance_km": 15,
    }
    assert client.get(nearby_url, params={**base_params, "latitude": 91}).status_code == 422
    assert client.get(nearby_url, params={**base_params, "longitude": -181}).status_code == 422
    assert client.get(nearby_url, params={**base_params, "distance_km": 0}).status_code == 422
    assert client.get(nearby_url, params={**base_params, "limit": 101}).status_code == 422


def test_get_update_and_delete_return_404_for_missing_or_deleted_address(
    client: TestClient,
) -> None:
    assert client.get("/api/v1/addresses/999").status_code == 404
    assert client.patch("/api/v1/addresses/999", json={"city": "Makati"}).status_code == 404
    assert client.delete("/api/v1/addresses/999").status_code == 404

    address_id = client.post("/api/v1/addresses", json=MANILA).json()["id"]
    assert client.delete(f"/api/v1/addresses/{address_id}").status_code == 204
    assert client.patch(f"/api/v1/addresses/{address_id}", json={"city": "Makati"}).status_code == 404
    assert client.delete(f"/api/v1/addresses/{address_id}").status_code == 404
