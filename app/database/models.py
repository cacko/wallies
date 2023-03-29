from peewee import Model, DoesNotExist
from .database import Database
from .fields import CategoryField, ColorField, ImageField, Source
from playhouse.shortcuts import model_to_dict
from peewee import CharField, IntegerField, DateTimeField, ForeignKeyField
from faker import Faker
from app.config import app_config
from pathlib import Path
from stringcase import spinalcase
from datetime import datetime, timezone


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
    Name = CharField(max_length=1000, default=get_default_name)
    Category = CategoryField()
    Image = ImageField()
    last_modified = DateTimeField(default=datetime.now(tz=timezone.utc))
    slug = CharField()
    Source = CharField(default=Source.MASHA.value)

    def save(self, *args, **kwds):
        self.slug = spinalcase(self.Name)
        return super().save(*args, **kwds)

    @property
    def raw_src(self) -> str:
        stem = (Path(self.Image)).stem
        return f"{CDN_ROOT}/{stem}.png.png"

    @property
    def webp_src(self) -> str:
        stem = (Path(self.Image)).stem
        return f"{CDN_ROOT}/{stem}.webp"

    @property
    def web_uri(self) -> str:
        return f"{app_config.api.web_host}/v/{self.slug}"

    class Meta:
        database = Database.db
        table_name = 'walls_artwork'
        order_by = ["-last_modified"]


class Artcolor(DbModel):
    Color = ColorField()
    Artwork = ForeignKeyField(Artwork)
    weight = IntegerField()

    class Meta:
        database = Database.db
        table_name = 'walls_artcolor'
        order_by = ["-weight"]
