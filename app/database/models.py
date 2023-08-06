from peewee import Model, DoesNotExist
from .database import Database
from .fields import CategoryField, AnimalField, ColorField, ImageField, Source
from playhouse.shortcuts import model_to_dict
from peewee import (
    CharField,
    IntegerField,
    DateTimeField,
    ForeignKeyField,
    BooleanField,
)
from faker import Faker
from app.config import app_config
from pathlib import Path
from stringcase import spinalcase
import datetime

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
    last_modified = DateTimeField(default=datetime.datetime.now)
    slug = CharField()
    Source = CharField(default=Source.MASHA.value)
    deleted = BooleanField(default=False)
    botyo_id = CharField(null=True)

    def delete_instance(self, recursive=False, delete_nullable=False):
        self.deleted = True
        self.last_modified = datetime.datetime.now()
        self.save(only=["deleted", "last_modified"])

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
    def thumb_src(self) -> str:
        stem = (Path(self.Image)).stem
        return f"{CDN_ROOT}/{stem}.thumbnail.webp"

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


class Cuteness(DbModel):
    Url = CharField(max_length=1000)
    Animal = AnimalField()
    last_modified = DateTimeField(default=datetime.datetime.now)
    deleted = BooleanField(default=False)

    class Meta:
        database = Database.db
        table_name = 'walls_cuteness'
        order_by = ["-last_modified"]
