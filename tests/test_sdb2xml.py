"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the sdb2xml module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import io
from pathlib import Path
from sdbtool.sdb2xml import convert as sdb2xml_convert, tagtype_to_xmltype
from sdbtool.apphelp import TagType


def test_databases():
    dbfolder = Path(__file__).parent
    got_files = []
    for dbfile in dbfolder.glob("*.sdb"):
        output = io.StringIO()
        sdb2xml_convert(str(dbfile), output)
        output.seek(0)
        xml_content = output.read()
        expect_result_file = dbfolder / (dbfile.name + ".xml")
        with expect_result_file.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        assert xml_content == expected_content
        got_files.append(dbfile.name)

    expected_files = ["game.sdb", "shim_db.sdb", "test.sdb", "testdb.sdb"]
    expected_files.sort()
    got_files.sort()
    assert got_files == expected_files, (
        f"Expected files: {expected_files}, got: {got_files}"
    )


def test_tagtype_to_xmltype():
    assert tagtype_to_xmltype(TagType.NULL) is None
    assert tagtype_to_xmltype(TagType.STRING) == "xs:string"
    assert tagtype_to_xmltype(TagType.STRINGREF) == "xs:string"
    assert tagtype_to_xmltype(TagType.LIST) is None
    assert tagtype_to_xmltype(TagType.BINARY) == "xs:base64Binary"
    assert tagtype_to_xmltype(TagType.QWORD) == "xs:unsignedLong"
    assert tagtype_to_xmltype(TagType.DWORD) == "xs:unsignedInt"
    assert tagtype_to_xmltype(TagType.WORD) == "xs:unsignedShort"
    assert tagtype_to_xmltype(TagType.BYTE) == "xs:byte"
