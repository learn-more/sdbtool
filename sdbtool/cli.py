from sdbtool import sdb2xml
import click

@click.command()
@click.version_option()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.File("w", encoding="utf-8"),
    default="-",
    help="Path to the output XML file, or '-' for stdout.",
)
def cli(input_file, output):
    sdb2xml(input_file, output)
