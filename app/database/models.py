from peewee import Model, DoesNotExist
from .database import Database
from .fields import CategoryField, ColorField
from playhouse.shortcuts import model_to_dict
from peewee import CharField, IntegerField, TimestampField, ForeignKeyField
from faker import Faker
from app.config import app_config
from pathlib import Path

CDN_ROOT = (
    f"https://{app_config.aws.cloudfront_host}"
    f"/{app_config.aws.media_location}"
)

fake = Faker()


def get_default_name():
    return fake.text(max_nb_chars=30).strip(".")


class DbModel(Model):
    @classmethod
    def fetch(cls, *query, **filters):
        try:
            return cls.get(*query, **filters)
        except DoesNotExist:
            return None

    def to_dict(self):
        return model_to_dict(self)


class Artwork(DbModel):
    Name = CharField(max_length=1000)
    Category = CategoryField()
    Image = CharField()
    last_modified = TimestampField()
    slug = CharField()
    Source = CharField()

    @property
    def raw_src(self) -> str:
        stem = (Path(self.Image)).stem
        return f"{CDN_ROOT}/{stem}.png.png"

    @property
    def muzei_src(self) -> str:
        stem = (Path(self.Image)).stem
        return f"{CDN_ROOT}/{stem}.muzei.png"

    @property
    def web_uri(self) -> str:
        return f"{app_config.api.web_host}/v/{self.slug}"

    class Meta:
        database = Database.db
        table_name = 'walls_artwork'


class Artcolor(DbModel):
    Color = ColorField()
    Artwork = ForeignKeyField(Artwork)
    weight = IntegerField()

    class Meta:
        database = Database.db
        table_name = 'walls_artcolor'
        order_by = ["-weight"]
