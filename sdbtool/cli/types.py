"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     click type for SDB database handling
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click

from sdbtool.apphelp import PathType, SdbDatabase


class SdbDatabaseParamType(click.ParamType):
    name = "sdb_database"

    def convert(self, value, param, ctx):
        if isinstance(value, SdbDatabase):
            return value

        try:
            db = SdbDatabase(value, PathType.DOS_PATH)
            if not db:
                db.close()
                raise ValueError(f"Failed to open database at '{value}'")

            if ctx:
                ctx.call_on_close(db.close)

            return db

        except ValueError as ex:
            self.fail(f"{value!r} is not a valid SDB database: {ex}", param, ctx)


SDB_DATABASE = SdbDatabaseParamType()
