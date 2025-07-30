"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the gui command
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.gui import show_gui


@click.command("gui")
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def command(ctx, input_file):
    """Launch the GUI for the SDB tool."""
    try:
        show_gui(input_file)
    except Exception as e:
        click.echo(f"Error launching GUI: {e}")
        ctx.exit(1)
