from pathlib import Path
from colorthief import ColorThief
import numpy as np
from functools import reduce
from corefile import TempPath
from PIL import Image


def int_to_rgb(color: int) -> tuple[int, ...]:
    return color >> 16 & 255, color >> 8 & 255, color & 255


def int_to_hex(rgb: int) -> str:
    return "{0:06X}".format(rgb)


def hex_to_int(color: str) -> int:
    return int(color, 16)


def hex_to_rgb(color: str) -> tuple[int, ...]:
    return int_to_rgb(hex_to_int(color))


def rgb_to_hex(rgb: tuple[int, ...]) -> str:
    return "{0:06X}".format(rgb_to_int(rgb))


def rgb_to_int(rgb: tuple[int, ...]) -> int:
    return rgb[0] << 16 | rgb[1] << 8 | rgb[2]


def color_dist(colors: list[tuple[int, ...]], color: tuple[int, ...]) -> int:
    if not len(colors):
        return 500
    np_colors = np.array(colors)
    np_color = np.array(color)
    distances = np.sqrt(np.sum((np_colors - np_color) ** 2, axis=1))
    return np.amin(distances)


def similar_colors(
    color: tuple[int, ...], colors: list[tuple[int, ...]], distance=70
) -> list[tuple[int, int, int]]:
    np_colors = np.array(colors)
    np_color = np.array(color)
    distances = np.sqrt(np.sum((np_colors - np_color) ** 2, axis=1))
    indexes = np.where(distances < distance)
    res = np_colors[indexes]
    return res.tolist()


def combine_colors(colors: list[int], tolerance=70) -> list[int]:
    return reduce(
        lambda r, x: [*r, int_to_rgb(x)]
        if color_dist(r, int_to_rgb(x)) > tolerance
        else r,
        colors,
        [],
    )


class DominantColorsMeta(type):
    colors_count = 5
    colors_quality = 1


class DominantColors(object, metaclass=DominantColorsMeta):

    colors_count = 5
    colors_quality = 10

    def __init__(self, image_path: Path, colors_count=5, colors_quality=1) -> None:
        self.__image_path = image_path
        self.colors_count = colors_count
        self.colors_quality = colors_quality
        super().__init__()

    @property
    def colors(self) -> list[tuple[int, ...]]:
        thumb_path = TempPath(f"{self.__image_path.name}-colors.jpg")
        img = Image.open(self.__image_path.as_posix())
        img.thumbnail((700, 700))
        img.save(thumb_path.as_posix())
        res = ColorThief(thumb_path.as_posix()).get_palette(
            self.colors_count, self.colors_quality)
        return res
