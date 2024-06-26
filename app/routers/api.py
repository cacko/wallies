from functools import reduce
import logging
from math import ceil, floor
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Request, Form, File
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
from app.config import app_config
from urllib.parse import urlencode

router = APIRouter()


def get_next_url(
    total: int,
    page: int,
    limit: int,
    last_modified: Optional[float] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
):
    try:
        last_page = ceil(total/limit)
        page += 1
        assert last_page + 1 > page
        params = {k: v for k, v in dict(
            page=page,
            limit=limit,
            category=category,
            color=color,
            last_modified=last_modified
        ).items() if v}
        return f"{app_config.api.web_host}/api/artworks?{urlencode(params)}"
    except AssertionError:
        return None


def get_list_response(
    category: Optional[str] = None,
    color: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    last_modified: Optional[float] = None
):
    results = []
    filters = [Artwork.deleted == False]
    order_by = []
    try:
        assert category
        categories = split_with_quotes(category, ",")
        assert categories
        f_categories = Category.to_categories(categories)
        assert f_categories
        filters.append(Artwork.Category.in_(f_categories))
    except AssertionError:
        pass

    if last_modified:
        filters.append(Artwork.last_modified >
                       datetime.fromtimestamp(last_modified))

    try:
        assert color
        colors = list(map(int, split_with_quotes(color, ",")))
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

    if page == -1:
        results = [dict(
            title=artwork.Name,
            raw_src=artwork.raw_src,
            web_uri=artwork.web_uri,
            webp_src=artwork.webp_src,
            thumb_src=artwork.thumb_src,
            category=artwork.Category,
            colors=artwork.colors,
            id=artwork.slug,
            last_modified=datetime.timestamp(artwork.last_modified),
            deleted=artwork.deleted
        ) for artwork in query.order_by(fn.Random()).limit(limit)]
        return JSONResponse(content=results)

    else:
        if len(order_by):
            query = query.order_by(*order_by)
        total = query.count()
        if total > 0:
            page = min(max(1, page), floor(total / limit) + 1)

        results = [dict(
            title=artwork.Name,
            raw_src=artwork.raw_src,
            web_uri=artwork.web_uri,
            webp_src=artwork.webp_src,
            thumb_src=artwork.thumb_src,
            category=artwork.Category,
            colors=artwork.colors,
            id=artwork.slug,
            last_modified=datetime.timestamp(artwork.last_modified),
            deleted=artwork.deleted
        ) for artwork in query.order_by(Artwork.last_modified.desc()).paginate(page, limit)]
        headers = {
            "x-pagination-total": f"{total}",
            "x-pagination-page": f"{page}",
        }
        if next_url := get_next_url(
                total=total,
                page=page,
                limit=limit,
                last_modified=last_modified,
                category=category,
                color=color
        ):
            headers["x-pagination-next"] = next_url
        return JSONResponse(content=results, headers=headers)


@router.get("/api/artworks", tags=["api"])
async def list_artworks(
    category: Optional[str] = None,
    color: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    last_modified: Optional[float] = None
):
    return get_list_response(
        category=category,
        color=color,
        page=page,
        limit=limit,
        last_modified=last_modified
    )


@router.get("/api/artwork/{title}", tags=["api"])
async def get_artwork(title: str):
    try:
        artwork = (
            Artwork
            .select(
                Artwork,
                fn.string_agg(Artcolor.Color.cast(
                    "text"), ",").alias("colors")
            ).join(Artcolor)
            .where((Artwork.slug == title) | (Artwork.botyo_id == title))
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
            id=artwork.slug,
            last_modified=datetime.timestamp(artwork.last_modified),
            deleted=artwork.deleted
        )
    except AssertionError:
        raise HTTPException(404)


@router.post("/api/artworks", tags=["api"])
def create_upload_file(
    request: Request,
    file: bytes = File(),
    category: str = Form(),
    botyo_id: str = Form()

):
    uploaded_path = TempPath(uuid4().hex)
    uploaded_path.write_bytes(file)
    with Database.db.atomic():
        obj = Artwork(
            Category=Category(category.lower()),
            Image=uploaded_path.as_posix(),
            botyo_id=botyo_id
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
        return obj.to_dict()
