from email.policy import default
import click
from typing import Optional
import logging
import sys
from app.core.palette import generate_palette


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
@click.option("-o", "--outpath", default=None)
def cli_palette(outpath: Optional[str] = None):
    generate_palette(outpath)


@cli.command("stats")
@click.option("-c", "--categories", is_flag=True, default=False)
def cli_stats(categories: bool):
    if categories:
        


@cli.command("quit")
def quit():
    """Quit."""
    output("Bye!", color="blue")
    sys.exit(0)


if __name__ == "__main__":
    cli()
