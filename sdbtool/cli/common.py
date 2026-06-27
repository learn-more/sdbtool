"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Shared CLI options and utilities for sdbtool commands
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

import click

AUTO_EXCLUDE = ["INDEXES", "STRINGTABLE"]


def expand_exclude(exclude: str) -> list[str]:
    """Parse and expand the --exclude option value, resolving the 'auto' alias."""
    tags = [c.strip() for c in exclude.split(",") if c.strip()]
    if "auto" in tags:
        tags.remove("auto")
        tags.extend(AUTO_EXCLUDE)
    return tags


def common_sdb_options(f):
    """Shared --exclude, --tagid, and --tag options for SDB conversion commands."""
    f = click.option(
        "--exclude",
        type=click.STRING,
        default="",
        metavar="TAG,TAG",
        help="Exclude specified tags from the SDB file."
        " Use 'auto' as an alias for 'INDEXES,STRINGTABLE'.",
    )(f)
    f = click.option(
        "--tagid/--no-tagid",
        default=False,
        help="Include tagids (index in the database) in the output.",
    )(f)
    f = click.option(
        "--tag/--no-tag", default=False, help="Include tag number in the output."
    )(f)
    return f
