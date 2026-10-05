from math import isclose

from app.services.address import AddressService


def test_haversine_returns_zero_for_identical_points() -> None:
    assert AddressService._haversine_km(14.5995, 120.9842, 14.5995, 120.9842) == 0


def test_haversine_calculates_manila_to_quezon_city_distance() -> None:
    distance = AddressService._haversine_km(14.5995, 120.9842, 14.6511, 121.0493)

    assert 5 < distance < 15


def test_haversine_handles_antipodal_points() -> None:
    distance = AddressService._haversine_km(0, 0, 0, 180)

    assert isclose(distance, 20015.0868, rel_tol=1e-6)
