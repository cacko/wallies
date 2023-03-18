from pathlib import Path
from app.config import app_config
from typing import Optional
from PIL import Image, ImageDraw
import math
from .colors import hex_to_int, combine_colors
from app.database.models import Artcolor


def generate_palette(outpath: Optional[str] = None):
    outroot = Path(outpath if outpath else app_config.api.assets)
    tolerance = 70
    size = 500
    output = outroot / "palette.png"
    colors = [hex_to_int(x.Color) for x in Artcolor.select()]
    combined_colors = combine_colors(colors, tolerance=tolerance)

    columns = 5
    width = int(min(len(combined_colors), columns) * size)
    height = int((math.floor(len(combined_colors) / columns) + 1) * size)

    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas = ImageDraw.Draw(result)
    for idx, color in enumerate(combined_colors):
        x = int((idx % columns) * size)
        y = int(math.floor(idx / columns) * size)
        canvas.rectangle([(x, y), (x + size - 1, y + size - 1)], fill=color)

    result.save(output.as_posix(), "PNG")
