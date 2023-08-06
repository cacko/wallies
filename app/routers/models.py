from pydantic import BaseModel
from app.database.fields import AnimalName


class Cuteness(BaseModel):
    Path: str
    Animal: AnimalName
