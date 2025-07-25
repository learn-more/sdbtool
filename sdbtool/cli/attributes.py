"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the attributes command
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.attributes import get_attributes


@click.command("attributes")
@click.argument("files", type=click.Path(exists=True, dir_okay=False), nargs=-1)
def command(files):
    """Display file attributes as recognized by AppHelp."""
    for file_name in files:
        try:
            attrs = get_attributes(file_name)
        except ValueError as e:
            click.echo(f"Error getting attributes for {file_name}: {e}")
            continue
        click.echo(f"Attributes for {file_name}:")
        if not attrs:
            click.echo("  No attributes found.")
            continue
        for attr in attrs:
            click.echo(f"  {attr}")
