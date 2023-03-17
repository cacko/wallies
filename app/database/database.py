from playhouse.db_url import parse
from playhouse.postgres_ext import PostgresqlExtDatabase
from app.config import app_config
from typing import Optional


class DatabaseMeta(type):
    _instance: Optional['Database'] = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    @property
    def db(cls) -> PostgresqlExtDatabase:
        return cls().get_db()


class Database(object, metaclass=DatabaseMeta):

    def __init__(self):
        parsed = parse(app_config.db.url)
        self.__db = PostgresqlExtDatabase(**parsed)

    def get_db(self) -> PostgresqlExtDatabase:
        return self.__db
