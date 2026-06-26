"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the sdb2json command
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.cli.types import SDB_DATABASE
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
    "--exclude",
    type=click.STRING,
    default="",
    metavar="TAG,TAG",
    help="Exclude specified tags from the SDB file."
    " Use 'auto' as an alias for 'INDEXES,STRINGTABLE'.",
)
@click.option(
    "--annotations/--no-annotations",
    default=True,
    help="Include annotations (e.g. decoded flag names, UUIDs) as 'comment' fields [default: enabled].",
)
@click.option(
    "--tagid/--no-tagid",
    default=False,
    help="Include tagids (index in the database) in the JSON output.",
)
@click.option(
    "--tag/--no-tag", default=False, help="Include tag number in the JSON output."
)
@click.pass_context
def command(ctx, input_file, output, exclude, annotations, tagid, tag):
    """Convert an SDB file to JSON format."""
    try:
        exclude = [c.strip() for c in exclude.split(",") if c.strip()]
        if "auto" in exclude:
            exclude.remove("auto")
            exclude.extend(["INDEXES", "STRINGTABLE"])
        sdb2json_convert(
            db=input_file,
            output_stream=output,
            exclude_tags=exclude,
            with_annotations=annotations,
            with_tagid=tagid,
            with_tag=tag,
        )
    except Exception as e:
        click.echo(f"Error converting SDB to JSON: {e}")
        ctx.exit(1)
