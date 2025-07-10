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
import pytest


@pytest.mark.parametrize(
    "db_name",
    ["game.sdb", "shim_db.sdb", "test.sdb", "testdb.sdb"],
)
def test_database(db_name):
    dbfolder = Path(__file__).parent / 'data'
    output = io.StringIO()
    sdb2xml_convert(str(dbfolder / db_name), output)
    output.seek(0)
    xml_content = output.read()
    expect_result_file = dbfolder / (db_name + ".xml")
    with expect_result_file.open("r", encoding="utf-8") as f:
        expected_content = f.read()
    assert xml_content == expected_content


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
