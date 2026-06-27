"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the sdb2json command
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.cli.types import SDB_DATABASE
from sdbtool.cli.common import common_sdb_options, expand_exclude
from sdbtool.sdb2json import convert as sdb2json_convert


@click.command("sdb2json")
@click.argument("input_file", type=SDB_DATABASE, required=True)
@click.option(
    "--output",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Path to the output JSON file, or '-' for stdout.",
)
@click.option(
    "--annotations/--no-annotations",
    default=True,
    help="Include annotations (e.g. decoded flag names, UUIDs) as 'comment' fields [default: enabled].",
)
@common_sdb_options
@click.pass_context
def command(ctx, input_file, output, annotations, exclude, tagid, tag):
    """Convert an SDB file to JSON format."""
    try:
        sdb2json_convert(
            db=input_file,
            output_stream=output,
            exclude_tags=expand_exclude(exclude),
            with_annotations=annotations,
            with_tagid=tagid,
            with_tag=tag,
        )
    except Exception as e:
        click.echo(f"Error converting SDB to JSON: {e}")
        ctx.exit(1)
