from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AddressBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=255)
    birthday: date
    home_number: str = Field(min_length=1, max_length=50)
    cellphone_number: str = Field(min_length=1, max_length=50)
    email: EmailStr
    notes: str | None = Field(default=None, max_length=2000)
    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    birthday: date | None = None
    home_number: str | None = Field(default=None, min_length=1, max_length=50)
    cellphone_number: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    notes: str | None = Field(default=None, max_length=2000)
    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @field_validator(
        "name",
        "birthday",
        "home_number",
        "cellphone_number",
        "email",
        "street",
        "city",
        "country",
        "latitude",
        "longitude",
    )
    @classmethod
    def reject_explicit_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class AddressRead(AddressBase):
    id: int


class PaginationDetails(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool


class AddressPage(BaseModel):
    items: list[AddressRead]
    pagination: PaginationDetails