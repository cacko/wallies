from peewee import CharField, IntegerField
from enum import StrEnum
from app.core.colors import int_to_hex


class Category(StrEnum):
    MINIMAL = "minimal"
    ABSTRACT = "abstract"
    MOVIES = "movies"
    SPORT = "sport"
    GAMES = "games"
    CARTOON = "cartoon"
    FANTASY = "fantasy"
    NATURE = "nature"
    WHATEVER = "whatever"

    @classmethod
    def values(cls):
        return [member.value for member in cls.__members__.values()]


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
