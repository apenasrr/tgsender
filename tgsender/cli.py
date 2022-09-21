"""Console script for tgsender."""
import sys

import click

from . import tgsender


@click.command()
def main(args=None):
    """Console script for tgsender."""
    click.echo(
        "Replace this message by putting your code into " "tgsender.cli.main"
    )
    click.echo("See click documentation at https://click.palletsprojects.com/")

    tgsender.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
