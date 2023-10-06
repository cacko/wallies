from peewee import CharField, IntegerField
from enum import StrEnum
from app.core.colors import int_to_hex
from app.core.s3 import S3
from uuid import uuid4
from pathlib import Path
from corefile import TempPath
from PIL import Image


class Category(StrEnum):
    MINIMAL = "minimal"
    ABSTRACT = "abstract"
    LANDSCAPE = "landscape"
    SPORT = "sport"
    GAMES = "games"
    CARTOON = "cartoon"
    FANTASY = "fantasy"
    NATURE = "nature"
    HORROR = "horror"
    WHATEVER = "whatever"

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]

    @classmethod
    def to_categories(cls, values: list[str]) -> list['Category']:
        return [cls(x.lower()) for x in values if x.lower() in cls.values()]


class Source(StrEnum):
    MASHA = "masha"


class CategoryField(CharField):

    def db_value(self, value: Category):
        return value.value

    def python_value(self, value):
        return Category(value)


class ColorField(IntegerField):

    def db_value(self, value) -> int:
        return value

    def python_value(self, value: str | int) -> str:
        if isinstance(value, int):
            return int_to_hex(value)
        return ','.join([int_to_hex(int(x)) for x in value.split(",")])


class ImageField(CharField):

    def db_value(self, value: str):
        image_path = Path(value)
        assert image_path.exists()
        stem = uuid4().hex

        raw_fname = f"{stem}.png.png"
        S3.upload(image_path, raw_fname)

        img = Image.open(image_path.as_posix())

        webp_fname = f"{stem}.webp"
        webp_path = TempPath(webp_fname)
        img.save(webp_path.as_posix())
        S3.upload(webp_path, webp_fname)

        img.thumbnail((300, 300))
        thumb_fname = f"{stem}.thumbnail.webp"
        thumb_path = TempPath(thumb_fname)
        img.save(thumb_path.as_posix())
        S3.upload(thumb_path, thumb_fname)

        return webp_fname

    def python_value(self, value):
        return value
