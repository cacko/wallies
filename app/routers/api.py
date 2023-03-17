import logging
from math import floor
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Request, Form, File
from app.database.fields import Category
from app.database.database import Database
from app.database.models import Artwork, Artcolor
from fastapi.responses import JSONResponse
from app.core.colors import (
    hex_to_rgb,
    int_to_rgb,
    similar_colors,
    rgb_to_int,
    DominantColors
)
from corefile import TempPath
from peewee import fn

router = APIRouter()


@router.get("/api/artworks.json", tags=["api"])
def list_artworks(
    request: Request,
    Category__in: Optional[str] = None,
    artcolors__Color__in: Optional[int] = None,
    page: int = 1,
    limit: int = 20
):
    results = []
    filters = [True]
    order_by = []
    if Category__in:
        try:
            category = Category(Category__in.lower())
            filters.append(Artwork.Category == category)
        except ValueError:
            pass

    if artcolors__Color__in:
        allcolors = [hex_to_rgb(x.Color)
                     for x in Artcolor.select(Artcolor.Color).distinct()]
        similar = [rgb_to_int(x) for x in similar_colors(
            int_to_rgb(artcolors__Color__in), allcolors)]
        logging.debug(f"similar colors to {artcolors__Color__in}, {similar}")
        filters.append(Artcolor.Color.in_(similar))
        order_by.append(-fn.SUM(Artcolor.weight))

    query = Artwork.select(
        Artwork,
        fn.string_agg(Artcolor.Color.cast("text"), ",").alias("colors")
    ).where(*filters).join(Artcolor).group_by(Artwork)

    if len(order_by):
        query = query.order_by(*order_by)

    total = query.count()
    page = min(max(1, page), floor(total / limit) + 1)
    for artwork in query.paginate(page, limit):
        results.append(
            dict(
                title=artwork.Name,
                raw_src=artwork.raw_src,
                muzei_src=artwork.muzei_src,
                web_uri=artwork.web_uri,
                category=artwork.Category,
                colors=artwork.colors,
            )
        )
    headers = {
        "X-Pagination-Total": f"{total}",
        "X-Pagination-Page": f"{page}",
    }
    return JSONResponse(content=results, headers=headers)


@router.post("/api/artworks.json", tags=["api"])
def create_upload_file(
    request: Request,
    file: bytes = File(),
    category: str = Form()

):
    uploaded_path = TempPath(uuid4().hex)
    uploaded_path.write_bytes(file)
    with Database.db.atomic():
        obj = Artwork(
            Category=Category(category.lower()),
            Image=uploaded_path.as_posix()
        )
        obj.save()
        colors = DominantColors(uploaded_path).colors
        Artcolor.bulk_create([
            Artcolor(
                Color=rgb_to_int(color),
                Artwork=obj,
                weight=2 ** (5 - idx)
            )
            for idx, color in enumerate(colors)
        ])
        logging.debug(obj)
        return ""
