"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Entrypoint of the sdbtool tool
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import sys
from pathlib import Path
from sdbtool.sdb2xml import convert as sdb2xml_convert, XmlAnnotations
from sdbtool.attributes import get_attributes
import typer
from rich import print


app = typer.Typer(help="A command-line tool for working with SDB files.", no_args_is_help=True, rich_markup_mode="markdown")

# CONTEXT_SETTINGS = dict(
#     max_content_width=200,
# )


# @click.group(
#     name="sdbtool",
#     help="A command-line tool for working with SDB files.",
#     context_settings=CONTEXT_SETTINGS,
# )
# @click.version_option()
# def sdbtool_command():
#     """sdbtool: A command-line tool for working with SDB files."""
#     pass  # pragma: no cover


@app.command("sdb2xml")
# @click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
# @click.option(
#     "--output",
#     type=click.File("w", encoding="utf-8"),
#     default="-",
#     help="Path to the output XML file, or '-' for stdout.",
# )
# @click.option(
#     "--exclude",
#     type=click.STRING,
#     default="",
#     metavar="TAG,TAG",
#     help="Exclude specified tags from the SDB file."
#     " Use 'auto' as an alias for 'INDEXES,STRINGTABLE'.",
# )
# @click.option(
#     "--annotations",
#     type=click.Choice(Annotations, case_sensitive=False),
#     default=Annotations.Comment,
#     show_default=True,
#     help="Specify the type of annotations to include in the XML output: 'Disabled' - no annotations. 'Comment' - annotations as comments.",
# )
def sdb2xml_command(
    input_file: Path = typer.Argument(dir_okay=False, show_default=False, help="Path to the input SDB file"),
    output: typer.FileTextWrite = typer.Option(encoding="utf8", allow_dash=True, default="-", help="Path to the output XML file"),
    exclude: str = typer.Option(default="", help="Comma-separated list of tags to exclude from the SDB file. Use 'auto' to exclude 'INDEXES,STRINGTABLE'."),
    annotations: XmlAnnotations = typer.Option(case_sensitive=False, default=XmlAnnotations.Comment, help="""Specify the type of annotations to include in the XML output:
 - 'Disabled' - no annotations.
 - 'Comment' - annotations as comments."""),
):
    """Convert an SDB file to XML format."""
    try:
        exclude_list = [c.strip() for c in exclude.split(",") if c.strip()]
        if "auto" in exclude_list:
            exclude_list.remove("auto")
            exclude_list.extend(["INDEXES", "STRINGTABLE"])
        sdb2xml_convert(
            input_file=input_file,
            output_stream=output,
            exclude_tags=exclude_list,
            annotations=annotations,
        )
    except Exception as e:
        print(f"Error converting SDB to XML: {e}")
        sys.exit(1)


@app.command("attributes")
def attributes_command(files: list[Path] = typer.Argument(dir_okay=False, help="List of SDB files to display attributes for.")):
    """Display file attributes as recognized by AppHelp."""
    for file_name in files:
        try:
            attrs = get_attributes(file_name)
        except ValueError as e:
            print(e)
            continue
        print(f"Attributes for {file_name}:")
        if not attrs:
            print("  No attributes found.")
            continue
        for attr in attrs:
            print(f"  {attr}")
