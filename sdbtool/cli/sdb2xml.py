"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     cli handling for the sdb2xml command
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from sdbtool.cli.types import SDB_DATABASE
from sdbtool.sdb2xml import convert as sdb2xml_convert, XmlAnnotations


@click.command("sdb2xml")
@click.argument("input_file", type=SDB_DATABASE, required=True)
@click.option(
    "--output",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Path to the output XML file, or '-' for stdout.",
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
    "--annotations",
    type=click.Choice(XmlAnnotations, case_sensitive=False),
    default=XmlAnnotations.Comment,
    show_default=False,
    help="Specify the type of annotations to include in the XML output [default: Comment]\n"
    " - Disabled: no annotations.\n"
    " - Comment: annotations as comments.",
)
@click.option(
    "--tagid/--no-tagid",
    default=False,
    help="Include tagids (index in the database) in the XML output.",
)
@click.option(
    "--tag/--no-tag", default=False, help="Include tag number in the XML output."
)
@click.pass_context
def command(ctx, input_file, output, exclude, annotations, tagid, tag):
    """Convert an SDB file to XML format."""
    try:
        exclude = [c.strip() for c in exclude.split(",") if c.strip()]
        if "auto" in exclude:
            exclude.remove("auto")
            exclude.extend(["INDEXES", "STRINGTABLE"])
        sdb2xml_convert(
            db=input_file,
            output_stream=output,
            exclude_tags=exclude,
            annotations=annotations,
            with_tagid=tagid,
            with_tag=tag,
        )
    except Exception as e:
        click.echo(f"Error converting SDB to XML: {e}")
        ctx.exit(1)
