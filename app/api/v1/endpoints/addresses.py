from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.dependencies import get_address_service
from app.schemas.address import (
    AddressCreate,
    AddressPage,
    AddressRead,
    AddressUpdate,
    PaginationDetails,
)
from app.services.address import AddressService

# Groups all address-related endpoints under the "/addresses" path
router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("", response_model=AddressRead, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: AddressCreate,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressRead:
    # Creates a new record to the address book and returns the created address
    return service.create_address(payload)


@router.get("", response_model=AddressPage)
def list_addresses(
    service: Annotated[AddressService, Depends(get_address_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AddressPage:
    # Gets a page of addresses (up to 100 at a time).
    addresses, total = service.list_addresses(limit=limit, offset=offset)
    # Returns the addresses along with paging info, including whether more pages remain
    return AddressPage(
        items=addresses,
        pagination=PaginationDetails(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(addresses) < total,
        ),
    )


@router.get("/nearby", response_model=AddressPage)
def list_nearby_addresses(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    distance_km: Annotated[float, Query(gt=0, description="Search radius in kilometres")],
    service: Annotated[AddressService, Depends(get_address_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AddressPage:
    # Finds addresses close to a given location (latitude and longitude),
    # within the distance in kilometres that the user chooses
    addresses, total = service.find_addresses_within_distance(
        latitude=latitude,
        longitude=longitude,
        distance_km=distance_km,
        limit=limit,
        offset=offset,
    )
    # Returns the nearby addresses along with paging info, same as the main list
    return AddressPage(
        items=addresses,
        pagination=PaginationDetails(
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(addresses) < total,
        ),
    )


@router.get("/{address_id}", response_model=AddressRead)
def get_address(
    address_id: int,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressRead:
    # Looks up a single address by its ID
    return service.get_address(address_id)


@router.patch("/{address_id}", response_model=AddressRead)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> AddressRead:
    # Changes some of the details of an existing address and returns the updated version
    return service.update_address(address_id, payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    service: Annotated[AddressService, Depends(get_address_service)],
) -> None:
    # Removes an address. Nothing is sent back once it's deleted.
    service.delete_address(address_id)