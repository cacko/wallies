from pydantic import BaseModel
from app.database.fields import AnimalName


class Cuteness(BaseModel):
    Url: str
    Animal: AnimalName
