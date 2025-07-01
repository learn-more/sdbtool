"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Entrypoint of the sdbtool tool, which converts SDB files to XML format.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import sdbtool.apphelp as apphelp
from pathlib import Path

from sdbtool.xml import XmlTagVisitor


def sdb2xml(input_file: str, output_stream):
    with apphelp.SdbDatabase(input_file, apphelp.PathType.DOS_PATH) as db:
        if not db:
            print(f"Failed to open database at '{input_file}'")
            return

        visitor = XmlTagVisitor(output_stream, Path(input_file).name)
        root = db.root()
        if root is None:
            print(f"No root tag found in database '{input_file}'")
            return
        root.accept(visitor)
