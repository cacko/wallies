from functools import reduce
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
from corestring import split_with_quotes
from corefile import TempPath
from peewee import fn
from app.scheduler import Scheduler
from app.core.palette import generate_palette
from datetime import datetime, timedelta, timezone

router = APIRouter()


def get_list_response(
    categories: Optional[list[str]] = None,
    colors: Optional[list[int]] = None,
    page: int = 1,
    limit: int = 20,
):
    results = []
    filters = [True]
    order_by = []
    try:
        logging.warning(f"CATEGORIES -> {categories}")
        assert categories
        f_categories = Category.to_categories(categories)
        logging.warning(f"CATEGORIES -> {f_categories}")
        assert f_categories
        filters.append(Artwork.Category.in_(f_categories))
    except AssertionError:
        pass

    try:
        assert colors
        allcolors = [hex_to_rgb(x.Color)
                     for x in Artcolor.select(Artcolor.Color).distinct()]
        assert allcolors
        similar: list[int] = reduce(
            lambda r, c: [
                *r,
                *[
                    rgb_to_int(x)
                    for x in similar_colors(int_to_rgb(c), allcolors)
                    if rgb_to_int(x) not in r
                ]
            ],
            colors,
            []
        )
        assert similar
        logging.debug(f"similar colors to {colors}, {similar}")
        filters.append(Artcolor.Color.in_(similar))
        order_by.append(-fn.SUM(Artcolor.weight))
    except AssertionError:
        pass

    base_query = Artwork.select(
        Artwork,
        fn.string_agg(Artcolor.Color.cast("text"), ",").alias("colors")
    )

    query = base_query.where(*filters).join(Artcolor).group_by(Artwork)

    if len(order_by):
        query = query.order_by(*order_by)

    total = query.count()
    if total > 0:
        page = min(max(1, page), floor(total / limit) + 1)
    else:
        total = limit
        page = 1
        query = base_query.order_by(fn.Random()).limit(total)
    results = [dict(
        title=artwork.Name,
        raw_src=artwork.raw_src,
        web_uri=artwork.web_uri,
        webp_src=artwork.webp_src,
        category=artwork.Category,
        colors=artwork.colors,
    ) for artwork in query.paginate(page, limit)]
    headers = {
        "X-Pagination-Total": f"{total}",
        "X-Pagination-Page": f"{page}",
    }
    return JSONResponse(content=results, headers=headers)


@router.get("/api/artworks", tags=["api"])
def list_artworks(
    category: Optional[str] = None,
    color: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    return get_list_response(
        categories=split_with_quotes(category, ",") if category else None,
        colors=list(map(int, split_with_quotes(color, ","))
                    ) if color else None,
        page=page,
        limit=limit
    )


@router.get("/api/artwork/{title}", tags=["api"])
def get_artwork(title: str):
    artwork = (
        Artwork
        .select(
            Artwork,
            fn.string_agg(Artcolor.Color.cast(
                "text"), ",").alias("colors")
        ).join(Artcolor)
        .where(Artwork.Name == title)
        .group_by(Artwork)
        .get()
    )
    assert artwork
    return dict(
        title=artwork.Name,
        raw_src=artwork.raw_src,
        web_uri=artwork.web_uri,
        webp_src=artwork.webp_src,
        category=artwork.Category,
        colors=artwork.colors,
    )


@router.get("/api/artworks.json", tags=["api"])
def list_artworks_django(
    request: Request,
    Category__in: Optional[str] = None,
    artcolors__Color__in: Optional[int] = None,
    page: int = 1,
    limit: int = 20
):
    return get_list_response(
        categories=[Category__in] if Category__in else None,
        colors=[artcolors__Color__in] if artcolors__Color__in else None,
        page=page,
        limit=limit
    )


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
        Scheduler.add_job(
            generate_palette,
            name="generate_palette",
            trigger='date',
            replace_existing=True,
            run_date=datetime.now(tz=timezone.utc) + timedelta(minutes=2)
        )
        return ""
