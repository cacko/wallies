from pydantic import BaseModel
from app.database.fields import AnimalName


class CutenessData(BaseModel):
    Path: str
    Animal: AnimalName
