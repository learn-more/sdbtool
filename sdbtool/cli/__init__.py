"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Entrypoint of the sdbtool tool
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.cli.sdb2xml import command as sdb2xml_command
from sdbtool.cli.attributes import command as attributes_command
import click


CONTEXT_SETTINGS = dict(
    max_content_width=200,
)


@click.group(
    name="sdbtool",
    help="A command-line tool for working with SDB files.",
    context_settings=CONTEXT_SETTINGS,
)
@click.version_option()
def sdbtool_command():
    """sdbtool: A command-line tool for working with SDB files."""
    pass  # pragma: no cover


sdbtool_command.add_command(sdb2xml_command)
sdbtool_command.add_command(attributes_command)
