"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Entrypoint of the sdbtool tool
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import sys
from sdbtool import sdb2xml
from sdbtool.attributes import get_attributes
import click


@click.group(name="sdbtool", help="A command-line tool for working with SDB files.")
@click.version_option()
def sdbtool_command():
    """sdbtool: A command-line tool for working with SDB files."""
    pass


@sdbtool_command.command("sdb2xml")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Path to the output XML file, or '-' for stdout.",
)
def sdb2xml_command(input_file, output):
    """Convert an SDB file to XML format."""
    try:
        sdb2xml.convert(input_file, output)
    except Exception as e:
        click.echo(f"Error converting SDB to XML: {e}")
        sys.exit(1)


@sdbtool_command.command("attributes")
@click.argument("files", type=click.Path(exists=True, dir_okay=False), nargs=-1)
def attributes_command(files):
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
