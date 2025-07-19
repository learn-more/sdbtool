"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the sdb2xml module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import io
from pathlib import Path
from sdbtool.sdb2xml import (
    XmlTagVisitor,
    convert as sdb2xml_convert,
    tagtype_to_xmltype,
)
from sdbtool.apphelp import TAGID_ROOT, PathType, SdbDatabase, Tag, TagType, winapi
import pytest

TESTDATA_FOLDER = Path(__file__).parent / "data"

ALL_TAGS_RESULT = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<SDB xmlns:xs="http://www.w3.org/2001/XMLSchema" file="all_tagtypes.sdb">
  <DATABASE>
    <InvalidTag></InvalidTag>
    <InvalidTag />
    <InvalidTag type="xs:byte">255</InvalidTag>
    <InvalidTag type="xs:unsignedShort">65535</InvalidTag>
    <InvalidTag type="xs:unsignedInt">4294967295</InvalidTag>
    <InvalidTag type="xs:unsignedLong">18446744073709551615</InvalidTag>
    <InvalidTag type="xs:base64Binary">//////////8=</InvalidTag>
    <InvalidTag type="xs:string"></InvalidTag>
    <InvalidTag type="xs:string"></InvalidTag>
    <DATABASE></DATABASE>
    <INCLUDE />
    <InvalidTag type="xs:byte">0</InvalidTag>
    <MATCH_MODE type="xs:unsignedShort">0</MATCH_MODE>
    <SIZE type="xs:unsignedInt">0</SIZE>
    <BIN_FILE_VERSION type="xs:unsignedLong">0</BIN_FILE_VERSION>
    <InvalidTag type="xs:base64Binary">AAAAAAAAAAA=</InvalidTag>
    <InvalidTag type="xs:string">val</InvalidTag>
    <NAME type="xs:string"></NAME>
    <LIBRARY>
      <INDEX_TAG type="xs:unsignedShort">14338<!-- INDEX_TAG --></INDEX_TAG>
      <INDEX_KEY type="xs:unsignedShort">14339<!-- INDEX_KEY --></INDEX_KEY>
      <INDEX_FLAGS type="xs:unsignedInt">3<!-- SHIMDB_INDEX_UNIQUE_KEY | SHIMDB_INDEX_TRAILING_CHARACTERS --></INDEX_FLAGS>
      <GUEST_TARGET_PLATFORM type="xs:unsignedInt">17<!-- X86 | ARM64 --></GUEST_TARGET_PLATFORM>
      <RUNTIME_PLATFORM type="xs:unsignedInt">34<!-- AMD64 | 0x20 --></RUNTIME_PLATFORM>
    </LIBRARY>
    <PATCH>
      <APP>
        <EXE>
          <LINK_DATE type="xs:unsignedInt">0</LINK_DATE>
          <UPTO_LINK_DATE type="xs:unsignedInt">1<!-- 1970-01-01 00:00:01 UTC --></UPTO_LINK_DATE>
          <FROM_LINK_DATE type="xs:unsignedInt">69922<!-- 1970-01-01 19:25:22 UTC --></FROM_LINK_DATE>
        </EXE>
        <TIME type="xs:unsignedLong">0</TIME>
        <TIME type="xs:unsignedLong">131560831927601799<!-- 2017-11-25T11:33:12.7601799Z --></TIME>
        <EXE_ID type="xs:base64Binary"></EXE_ID>
        <EXE_ID type="xs:base64Binary">iHdmVSIRIhERIjNEVWZ3iA==<!-- {55667788-1122-1122-1122-334455667788} --></EXE_ID>
      </APP>
    </PATCH>
  </DATABASE>
</SDB>"""


def test_database():
    output = io.StringIO()
    sdb2xml_convert(str(TESTDATA_FOLDER / "all_tagtypes.sdb"), output, exclude_tags=[])
    output.seek(0)
    xml_content = output.read()
    assert xml_content == ALL_TAGS_RESULT


def test_database_with_exclude_tags():
    output = io.StringIO()
    sdb2xml_convert(
        str(TESTDATA_FOLDER / "all_tagtypes.sdb"),
        output,
        exclude_tags=["PATCH", "APP", "BIN_FILE_VERSION", "TIME"],
    )
    output.seek(0)
    xml_content = output.read()
    assert "INDEXES" not in xml_content
    assert "BIN_FILE_VERSION" not in xml_content
    assert "LINK_DATE" not in xml_content


def test_invalid_database():
    with pytest.raises(FileNotFoundError):
        sdb2xml_convert(
            str(TESTDATA_FOLDER / "non_existent.sdb"), io.StringIO(), exclude_tags=[]
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


def test_XmlTagVisitor_invalid_visit(monkeypatch):
    def mock_SdbOpenDatabase(path, type):
        return None

    monkeypatch.setattr(winapi, "SdbOpenDatabase", mock_SdbOpenDatabase)

    visitor = XmlTagVisitor(io.StringIO(), "test.sdb", exclude_tags=[])
    db = SdbDatabase("test.sdb", PathType.DOS_PATH)
    tag = Tag(db=db, tag_id=TAGID_ROOT)  #
    tag.type = TagType.LIST  # Invalid type for visit method
    tag.name = "TestTag"
    with pytest.raises(ValueError, match="Unknown xml tag type: LIST for tag TestTag"):
        visitor.visit(tag)
