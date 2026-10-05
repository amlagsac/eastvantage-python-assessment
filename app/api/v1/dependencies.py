from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.address import AddressService


def get_address_service(db: Annotated[Session, Depends(get_db)]) -> AddressService:
    """ 
        Gets a database connection and uses it to create the address service,
        so any route that needs address features can use it easily. 
    """
    return AddressService(db)