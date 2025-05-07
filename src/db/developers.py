from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import INET
from sqlmodel import Field, SQLModel, String

from src.db.mixins import UUIDMixin


class Developer(UUIDMixin, SQLModel, table=True):
    __tablename__ = "developers"
    name: str = Field(sa_type=String(280))
    last_known_ip: str = Field(sa_type=INET)
    department: str = Field(sa_type=String(280))
    is_available: bool
    geolocation: str = Field(sa_type=Geometry(geometry_type="POINT", srid=4326))
