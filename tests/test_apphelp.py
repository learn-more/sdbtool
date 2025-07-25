"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the apphelp module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import (
    TAGID_ROOT,
    SdbDatabase,
    PathType,
    Tag,
    guid_to_string,
    tag_value_to_string,
)
from base64 import b64decode
import pytest


def test_guid_to_string():
    # Test with a valid GUID
    guid_str = "Wy8It8yzrESgMGnvPjUiXQ=="
    guid = b64decode(guid_str)
    expected = "b7082f5b-b3cc-44ac-a030-69ef3e35225d"
    assert guid_to_string(guid) == expected

    # Test with an invalid GUID length
    with pytest.raises(ValueError, match="GUID must be 16 bytes long"):
        guid_to_string(bytes.fromhex("12345678"))


def test_read_wrong_types():
    db = SdbDatabase("db_does_not_exist.sdb", PathType.DOS_PATH)
    # Abuse a fake 'root' tag to test reading wrong types
    tag = Tag(db, TAGID_ROOT)
    with pytest.raises(ValueError, match="Tag SDB is not a BYTE type"):
        tag.read_byte()
    with pytest.raises(ValueError, match="Tag SDB is not a WORD type"):
        tag.read_word()
    with pytest.raises(ValueError, match="Tag SDB is not a DWORD type"):
        tag.read_dword()
    with pytest.raises(ValueError, match="Tag SDB is not a QWORD type"):
        tag.read_qword()
    with pytest.raises(ValueError, match="Tag SDB is not a BINARY type"):
        tag.read_bytes()
    with pytest.raises(ValueError, match="Tag SDB is not a STRING or STRINGREF type"):
        tag.read_string()
    with pytest.raises(ValueError, match="Unknown tag type: LIST for tag SDB"):
        tag_value_to_string(tag)


def test_ensure_db_handle():
    db = SdbDatabase("db_does_not_exist.sdb", PathType.DOS_PATH)
    assert db.root() is None
    fake_tag = Tag(db, TAGID_ROOT)
    with pytest.raises(ValueError, match="Database handle is not initialized"):
        fake_tag._ensure_db_handle()
