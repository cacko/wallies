import logging
from math import floor
from typing import Optional
from fastapi import APIRouter, Request
from app.database.fields import Category
from app.database.models import Artwork, Artcolor
from fastapi.responses import JSONResponse
from app.core.colors import hex_to_rgb, similar_colors, rgb_to_int
from peewee import fn

router = APIRouter()


@router.get("/api/artworks.json", tags=["api"])
def list_artworks(
    request: Request,
    Category__in: Optional[str] = None,
    artcolors__Color__in: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    results = []
    filters = [True]
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
            hex_to_rgb(artcolors__Color__in), allcolors)]
        logging.debug(f"similar colors to {artcolors__Color__in}, {similar}")
        color_artist = Artcolor.select(Artcolor.Artwork).where(
            Artcolor.Color.in_(similar))
        filters.append(Artwork.id.in_(color_artist))
    query = Artwork.select(
        Artwork,
        fn.string_agg(Artcolor.Color.cast("text"), ",").alias("colors")
    ).where(*filters).join(Artcolor).group_by(Artwork)

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
                colors=artwork.colors
            )
        )
    headers = {
        "X-Pagination-Total": f"{total}",
        "X-Pagination-Page": f"{page}",
    }
    return JSONResponse(content=results, headers=headers)
