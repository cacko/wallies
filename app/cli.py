from pathlib import Path
import click
from typing import Optional
import logging
import sys
import math
from app.database.models import Artcolor
from app.core.colors import combine_colors, hex_to_int
from PIL import Image, ImageDraw


def output(txt: str, color="bright_blue"):
    click.secho(txt, fg=color)


def error(e: Exception, txt: Optional[str] = None):
    if not txt:
        txt = f"{e}"
    click.secho(txt, fg="bright_red", err=True)
    if e:
        logging.debug(txt, exc_info=e)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        from app.main import serve
        output("App started")
        serve()


@cli.command("palette")
def cli_palette():
    tolerance = 70
    size = 500
    output = Path(__file__).parent.parent / "wallies_palette.png"
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


@cli.command("quit")
def quit():
    """Quit."""
    output("Bye!", color="blue")
    sys.exit(0)


if __name__ == "__main__":
    cli()
