"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the info command
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.info import get_info


@click.command("info")
@click.argument("files", type=click.Path(exists=True, dir_okay=False), nargs=-1)
def command(files):
    """Display file info for sdb files."""
    for file_name in files:
        try:
            info = get_info(file_name)
        except ValueError as e:
            click.echo(f"Error getting info for {file_name}: {e}")
            continue
        click.echo(f"Info for {file_name}:")
        click.echo(f"  Description: {info.Description or 'N/A'}")
        click.echo(f"  Version: {info.dwMajor}.{info.dwMinor}")
        click.echo(f"  Flags: {info.dwFlags:#x}")
        click.echo(f"  ID: {info.Id or 'N/A'}")
        click.echo(f"  Runtime Platform: {info.dwRuntimePlatform or 'N/A'}")
