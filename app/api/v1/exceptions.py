class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = 500


class AddressNotFoundError(AppError):
    status_code = 404

    def __init__(self, address_id: int) -> None:
        self.address_id = address_id
        super().__init__(f"Address {address_id} was not found")


class DuplicateEmailError(AppError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("An address with this email already exists")