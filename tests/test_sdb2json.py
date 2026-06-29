"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the sdb2json module.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

import io
import json
from pathlib import Path
from sdbtool.sdb2json import (
    JsonTagVisitor,
    convert as sdb2json_convert,
    tagtype_to_jsontype,
)
from sdbtool.apphelp import TAGID_ROOT, PathType, SdbDatabase, Tag, TagType, winapi
import pytest

TESTDATA_FOLDER = Path(__file__).parent / "data"

ALL_TAGS_RESULT = """{
  "file": "all_tagtypes.sdb",
  "children": [
    {
      "tag": "DATABASE",
      "children": [
        {
          "tag": "InvalidTag_0x7000",
          "children": []
        },
        {
          "tag": "InvalidTag_0x1000",
          "type": "null"
        },
        {
          "tag": "InvalidTag_0x2000",
          "type": "byte",
          "value": "255"
        },
        {
          "tag": "InvalidTag_0x3000",
          "type": "word",
          "value": "65535"
        },
        {
          "tag": "InvalidTag_0x4000",
          "type": "dword",
          "value": "4294967295"
        },
        {
          "tag": "InvalidTag_0x5000",
          "type": "qword",
          "value": "18446744073709551615"
        },
        {
          "tag": "InvalidTag_0x9000",
          "type": "binary",
          "value": "//////////8="
        },
        {
          "tag": "InvalidTag_0x8000",
          "type": "string",
          "value": ""
        },
        {
          "tag": "InvalidTag_0x6000",
          "type": "string",
          "value": ""
        },
        {
          "tag": "DATABASE",
          "children": []
        },
        {
          "tag": "INCLUDE",
          "type": "null"
        },
        {
          "tag": "InvalidTag_0x2001",
          "type": "byte",
          "value": "0"
        },
        {
          "tag": "MATCH_MODE",
          "type": "word",
          "value": "0"
        },
        {
          "tag": "SIZE",
          "type": "dword",
          "value": "0"
        },
        {
          "tag": "BIN_FILE_VERSION",
          "type": "qword",
          "value": "0"
        },
        {
          "tag": "InvalidTag_0x9001",
          "type": "binary",
          "value": "AAAAAAAAAAA="
        },
        {
          "tag": "InvalidTag_0x8001",
          "type": "string",
          "value": "val"
        },
        {
          "tag": "NAME",
          "type": "string",
          "value": ""
        },
        {
          "tag": "LIBRARY",
          "children": [
            {
              "tag": "INDEX_TAG",
              "type": "word",
              "value": "14338",
              "comment": "INDEX_TAG"
            },
            {
              "tag": "INDEX_KEY",
              "type": "word",
              "value": "14339",
              "comment": "INDEX_KEY"
            },
            {
              "tag": "INDEX_FLAGS",
              "type": "dword",
              "value": "3",
              "comment": "SHIMDB_INDEX_UNIQUE_KEY | SHIMDB_INDEX_TRAILING_CHARACTERS"
            },
            {
              "tag": "GUEST_TARGET_PLATFORM",
              "type": "dword",
              "value": "17",
              "comment": "X86 | ARM64"
            },
            {
              "tag": "RUNTIME_PLATFORM",
              "type": "dword",
              "value": "34",
              "comment": "AMD64 | 0x20"
            }
          ]
        },
        {
          "tag": "PATCH",
          "children": [
            {
              "tag": "APP",
              "children": [
                {
                  "tag": "EXE",
                  "children": [
                    {
                      "tag": "LINK_DATE",
                      "type": "dword",
                      "value": "0"
                    },
                    {
                      "tag": "UPTO_LINK_DATE",
                      "type": "dword",
                      "value": "1",
                      "comment": "1970-01-01 00:00:01 UTC"
                    },
                    {
                      "tag": "FROM_LINK_DATE",
                      "type": "dword",
                      "value": "69922",
                      "comment": "1970-01-01 19:25:22 UTC"
                    }
                  ]
                },
                {
                  "tag": "TIME",
                  "type": "qword",
                  "value": "0"
                },
                {
                  "tag": "TIME",
                  "type": "qword",
                  "value": "131560831927601799",
                  "comment": "2017-11-25T11:33:12.7601799Z"
                },
                {
                  "tag": "EXE_ID",
                  "type": "binary",
                  "value": ""
                },
                {
                  "tag": "EXE_ID",
                  "type": "binary",
                  "value": "iHdmVSIRIhERIjNEVWZ3iA==",
                  "comment": "{55667788-1122-1122-1122-334455667788}"
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
"""

STRIPPED_TAG_TAGID_RESULT = """{
  "file": "all_tagtypes.sdb",
  "tagid": 0,
  "tag_num": "0x0",
  "children": [
    {
      "tag": "DATABASE",
      "tagid": 12,
      "tag_num": "0x7001",
      "children": [
        {
          "tag": "DATABASE",
          "tagid": 78,
          "tag_num": "0x7001",
          "children": []
        },
        {
          "tag": "INCLUDE",
          "type": "null",
          "tagid": 84,
          "tag_num": "0x1001"
        },
        {
          "tag": "MATCH_MODE",
          "type": "word",
          "value": "0",
          "tagid": 90,
          "tag_num": "0x3001"
        },
        {
          "tag": "SIZE",
          "type": "dword",
          "value": "0",
          "tagid": 94,
          "tag_num": "0x4001"
        },
        {
          "tag": "BIN_FILE_VERSION",
          "type": "qword",
          "value": "0",
          "tagid": 100,
          "tag_num": "0x5002"
        },
        {
          "tag": "NAME",
          "type": "string",
          "value": "",
          "tagid": 138,
          "tag_num": "0x6001"
        },
        {
          "tag": "LIBRARY",
          "tagid": 144,
          "tag_num": "0x7002",
          "children": [
            {
              "tag": "INDEX_TAG",
              "type": "word",
              "value": "14338",
              "tagid": 150,
              "tag_num": "0x3802"
            },
            {
              "tag": "INDEX_KEY",
              "type": "word",
              "value": "14339",
              "tagid": 154,
              "tag_num": "0x3803"
            },
            {
              "tag": "INDEX_FLAGS",
              "type": "dword",
              "value": "3",
              "tagid": 158,
              "tag_num": "0x4016"
            },
            {
              "tag": "GUEST_TARGET_PLATFORM",
              "type": "dword",
              "value": "17",
              "tagid": 164,
              "tag_num": "0x4023"
            },
            {
              "tag": "RUNTIME_PLATFORM",
              "type": "dword",
              "value": "34",
              "tagid": 170,
              "tag_num": "0x4021"
            }
          ]
        }
      ]
    }
  ]
}
"""


@pytest.fixture(scope="module")
def all_tags_sdb():
    db = SdbDatabase(TESTDATA_FOLDER / "all_tagtypes.sdb")
    assert db
    yield db
    db.close()


def test_database(all_tags_sdb):
    output = io.StringIO()
    sdb2json_convert(
        db=all_tags_sdb,
        output_stream=output,
        exclude_tags=[],
        with_annotations=True,
        with_tagid=False,
        with_tag=False,
    )
    assert output.getvalue() == ALL_TAGS_RESULT


def test_database_with_exclude_tags(all_tags_sdb):
    output = io.StringIO()
    sdb2json_convert(
        db=all_tags_sdb,
        output_stream=output,
        exclude_tags=["PATCH", "APP", "BIN_FILE_VERSION", "TIME"],
        with_annotations=True,
        with_tagid=False,
        with_tag=False,
    )
    data = json.loads(output.getvalue())
    db_children = data["children"][0]["children"]
    tags = [c["tag"] for c in db_children]
    assert "PATCH" not in tags
    assert "BIN_FILE_VERSION" not in tags
    # LINK_DATE lives inside PATCH > APP > EXE which is excluded
    assert all(c["tag"] != "LINK_DATE" for c in db_children)


def test_no_annotations(all_tags_sdb):
    output = io.StringIO()
    sdb2json_convert(
        db=all_tags_sdb,
        output_stream=output,
        exclude_tags=[],
        with_annotations=False,
        with_tagid=False,
        with_tag=False,
    )
    data = json.loads(output.getvalue())
    library = next(
        c for c in data["children"][0]["children"] if c.get("tag") == "LIBRARY"
    )
    index_tag = next(c for c in library["children"] if c["tag"] == "INDEX_TAG")
    assert "comment" not in index_tag
    index_flags = next(c for c in library["children"] if c["tag"] == "INDEX_FLAGS")
    assert "comment" not in index_flags


def test_tagtype_to_jsontype():
    assert tagtype_to_jsontype(TagType.NULL) is None
    assert tagtype_to_jsontype(TagType.LIST) is None
    assert tagtype_to_jsontype(TagType.STRING) == "string"
    assert tagtype_to_jsontype(TagType.STRINGREF) == "string"
    assert tagtype_to_jsontype(TagType.BINARY) == "binary"
    assert tagtype_to_jsontype(TagType.QWORD) == "qword"
    assert tagtype_to_jsontype(TagType.DWORD) == "dword"
    assert tagtype_to_jsontype(TagType.WORD) == "word"
    assert tagtype_to_jsontype(TagType.BYTE) == "byte"


def test_JsonTagVisitor_invalid_visit(monkeypatch):
    def mock_SdbOpenDatabase(path, path_type):
        return None

    monkeypatch.setattr(winapi, "SdbOpenDatabase", mock_SdbOpenDatabase)

    visitor = JsonTagVisitor(
        "test.sdb",
        with_annotations=True,
        with_tagid=False,
        with_tag=False,
    )
    db = SdbDatabase("test.sdb", PathType.DOS_PATH)
    tag = Tag(db=db, tag_id=TAGID_ROOT)
    tag.type = TagType.LIST
    tag.name = "TestTag"
    tag.tag_id = 1  # non-root so the branch is hit
    with pytest.raises(ValueError, match="Unknown json tag type: LIST for tag TestTag"):
        visitor.visit(tag)


def test_convert_raises_when_root_is_none(monkeypatch):
    def mock_SdbOpenDatabase(path, path_type):
        return None

    monkeypatch.setattr(winapi, "SdbOpenDatabase", mock_SdbOpenDatabase)

    db = SdbDatabase("test.sdb", PathType.DOS_PATH)
    with pytest.raises(RuntimeError, match="Failed to get root tag from database"):
        sdb2json_convert(
            db=db,
            output_stream=io.StringIO(),
            exclude_tags=[],
            with_annotations=False,
            with_tagid=False,
            with_tag=False,
        )


def test_db_with_tagid_and_tag(all_tags_sdb):
    output = io.StringIO()
    sdb2json_convert(
        db=all_tags_sdb,
        output_stream=output,
        exclude_tags=["PATCH", "InvalidTag"],
        with_annotations=False,
        with_tagid=True,
        with_tag=True,
    )
    assert output.getvalue() == STRIPPED_TAG_TAGID_RESULT


class _FakeTag:
    """Minimal duck-typed Tag for exercising the visitor name handling."""

    def __init__(self, name, type_, tag=0x0, tag_id=0):
        self.name = name
        self.type = type_
        self.tag = tag
        self.tag_id = tag_id


def test_json_normalizes_tag_names():
    v = JsonTagVisitor(
        "f.sdb", with_annotations=False, with_tagid=False, with_tag=False
    )
    v.visit(_FakeTag("EXE_ID(GUID)", TagType.NULL))
    # Leading digit is fine in JSON, so it is kept (no "S" prefix).
    v.visit(_FakeTag("16BIT_DESCRIPTION", TagType.NULL))
    v.visit_list_begin(_FakeTag("MSI TRANSFORM", TagType.LIST, tag_id=1))
    v.visit_list_end(_FakeTag("MSI TRANSFORM", TagType.LIST, tag_id=1))
    names = [c["tag"] for c in v.result()["children"]]
    assert names == ["EXE_ID", "16BIT_DESCRIPTION", "MSI_TRANSFORM"]
