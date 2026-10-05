import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.exceptions import AddressNotFoundError, DuplicateEmailError
from app.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate
from math import asin, cos, radians, sin, sqrt

logger = logging.getLogger(__name__)
EARTH_RADIUS_KM = 6371.0


class AddressService:
    def __init__(self, db: Session) -> None:
        """Initialize the address service with the dependency-injected database session."""
        self.db = db

    def create_address(self, payload: AddressCreate) -> Address:
        """Create an address after normalizing and checking its unique email.

        Args:
            payload: The address data to create.

        Returns:
            The created address.
        """
        values = payload.model_dump()
        values["email"] = str(values["email"]).lower()
        self._ensure_email_available(values["email"])
        address = Address(**values)
        self.db.add(address)
        self._commit_email_change(values["email"])
        self.db.refresh(address)
        # Log the record identifier but not contact or location data.
        logger.info("Created address id=%s", address.id)
        return address

    def get_address(self, address_id: int) -> Address:
        """Return an active address by ID or raise when it is missing or deleted.

        Args:
            address_id: The ID of the address to get.

        Returns:
            The active address.
        """
        address = self.db.get(Address, address_id)
        if address is None or address.deleted_at is not None:
            raise AddressNotFoundError(address_id)
        return address

    def list_addresses(self, limit: int, offset: int) -> tuple[list[Address], int]:
        """Return a page of active addresses and the total active-address count.

        Args:
            limit: The number of addresses to return.
            offset: The offset of the addresses to return.

        Returns:
            A tuple containing the list of active addresses and the total active-address count.
        """
        active_addresses = select(Address).where(Address.deleted_at.is_(None))
        addresses = list(
            self.db.scalars(
                active_addresses.order_by(Address.id).offset(offset).limit(limit)
            ).all()
        )
        total = self.db.scalar(
            select(func.count()).select_from(active_addresses.subquery())
        )
        total = total or 0
        # Record page size and total for usage monitoring without logging address contents.
        logger.info(
            "Listed addresses returned=%s total=%s limit=%s offset=%s",
            len(addresses),
            total,
            limit,
            offset,
        )
        return addresses, total

    def update_address(self, address_id: int, payload: AddressUpdate) -> Address:
        """Apply supplied fields to an active address and persist the changes.

        Args:
            address_id: The ID of the address to update.
            payload: The address data to update.

        Returns:
            The updated address.
        """
        address = self.get_address(address_id)
        values = payload.model_dump(exclude_unset=True)
        email = values.get("email")
        if email is not None:
            email = str(email).lower()
            values["email"] = email
            self._ensure_email_available(email, exclude_id=address_id)
        for field, value in values.items():
            setattr(address, field, value)
        if email is not None:
            self._commit_email_change(email)
        else:
            self.db.commit()
        self.db.refresh(address)
        # Field names aid diagnostics while keeping submitted values private.
        logger.info("Updated address id=%s fields=%s", address_id, sorted(values))
        return address

    def delete_address(self, address_id: int) -> None:
        """Soft-delete an active address and change its original email for reuse.

        Args:
            address_id: The ID of the address to delete.
        """
        address = self.get_address(address_id)
        address.deleted_at = datetime.now(timezone.utc)
        address.email = f"deleted-{uuid4().hex}@deleted.invalid"
        self.db.commit()
        # Record the soft-delete operation without exposing the original email.
        logger.info("Soft-deleted address id=%s", address_id)

    def find_addresses_within_distance(
        self,
        latitude: float,
        longitude: float,
        distance_km: float,
        limit: int,
        offset: int,
    ) -> tuple[list[Address], int]:
        """Return a page of active addresses within the radius and the match count."""
        active = self.db.scalars(
            select(Address).where(Address.deleted_at.is_(None)).order_by(Address.id)
        ).all()
        matches = [
            a for a in active
            if self._haversine_km(latitude, longitude, a.latitude, a.longitude) <= distance_km
        ]
        total = len(matches)
        page = matches[offset : offset + limit]
        logger.info(
            "Nearby search radius_km=%s returned=%s matched=%s limit=%s offset=%s",
            distance_km,
            len(page),
            total,
            limit,
            offset,
        )
        return page, total

    def _ensure_email_available(self, email: str, exclude_id: int | None = None) -> None:
        """Raise when another address is already existing."""
        statement = select(Address.id).where(func.lower(Address.email) == email)
        if exclude_id is not None:
            statement = statement.where(Address.id != exclude_id)
        if self.db.scalar(statement) is not None:
            raise DuplicateEmailError()

    def _commit_email_change(self, email: str) -> None:
        """Commit a new email and translate unique-constraint into a conflict."""
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if self.db.scalar(
                select(Address.id).where(func.lower(Address.email) == email)
            ) is not None:
                raise DuplicateEmailError() from None
            # Keep unexpected database failures visible to the request error logger.
            raise

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Return the circle distance in kilometers between two points (latitude, longitude)."""
        phi1, lambda1, phi2, lambda2 = map(radians, [lat1, lon1, lat2, lon2])
        d_phi: float = phi2 - phi1
        d_lambda: float = lambda2 - lambda1
        a: float = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
        # Floating-point rounding can put antipodal distances just outside asin's domain.
        a = min(1.0, max(0.0, a))
        return 2 * EARTH_RADIUS_KM * asin(sqrt(a))
