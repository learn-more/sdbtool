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
    tag_value_to_string,
    tag_id_to_string,
)
import pytest


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


def test_tag_id_to_string():
    # TAG_TYPE_NULL
    assert tag_id_to_string(0x1000) == "InvalidTag"
    assert tag_id_to_string(0x1001) == "INCLUDE"
    assert tag_id_to_string(0x1002) == "GENERAL"
    assert tag_id_to_string(0x1003) == "MATCH_LOGIC_NOT"
    assert tag_id_to_string(0x1004) == "APPLY_ALL_SHIMS"

    # TAG_TYPE_WORD
    assert tag_id_to_string(0x3000) == "InvalidTag"
    assert tag_id_to_string(0x3001) == "MATCH_MODE"
    assert tag_id_to_string(0x3002) == "QUIRK_COMPONENT_CODE_ID"
    assert tag_id_to_string(0x3003) == "QUIRK_CODE_ID"
    assert tag_id_to_string(0x3801) == "TAG"
    assert tag_id_to_string(0x3802) == "INDEX_TAG"
    assert tag_id_to_string(0x3803) == "INDEX_KEY"

    # TAG_TYPE_DWORD
    assert tag_id_to_string(0x4000) == "InvalidTag"
    assert tag_id_to_string(0x4001) == "SIZE"
    assert tag_id_to_string(0x4002) == "OFFSET"
    assert tag_id_to_string(0x4003) == "CHECKSUM"
    assert tag_id_to_string(0x4004) == "SHIM_TAGID"
    assert tag_id_to_string(0x4016) == "INDEX_FLAGS"
    assert tag_id_to_string(0x401D) == "LINK_DATE"
    assert tag_id_to_string(0x401E) == "UPTO_LINK_DATE"
    assert tag_id_to_string(0x4023) == "GUEST_TARGET_PLATFORM"  # AKA OS_PLATFORM
    assert tag_id_to_string(0x4030) == "CONTEXT_TAGID"
    assert tag_id_to_string(0x4031) == "EXE_WRAPPER"
    assert tag_id_to_string(0x4032) == "EXE_TYPE"
    assert tag_id_to_string(0x4033) == "FROM_LINK_DATE"

    # TAG_TYPE_QWORD
    assert tag_id_to_string(0x5000) == "InvalidTag"
    assert tag_id_to_string(0x5001) == "TIME"
    assert tag_id_to_string(0x5002) == "BIN_FILE_VERSION"
    assert tag_id_to_string(0x5003) == "BIN_PRODUCT_VERSION"
    assert tag_id_to_string(0x5004) == "MODTIME"
    assert tag_id_to_string(0x5005) == "FLAG_MASK_KERNEL"
    assert tag_id_to_string(0x5006) == "UPTO_BIN_PRODUCT_VERSION"
    assert tag_id_to_string(0x5007) == "DATA_QWORD"
    assert tag_id_to_string(0x5008) == "FLAG_MASK_USER"
    assert tag_id_to_string(0x5009) == "FLAGS_NTVDM1"
    assert tag_id_to_string(0x500A) == "FLAGS_NTVDM2"
    assert tag_id_to_string(0x500B) == "FLAGS_NTVDM3"
    assert tag_id_to_string(0x500C) == "FLAG_MASK_SHELL"
    assert tag_id_to_string(0x500D) == "UPTO_BIN_FILE_VERSION"
    assert tag_id_to_string(0x500E) == "FLAG_MASK_FUSION"
    assert tag_id_to_string(0x500F) == "FLAG_PROCESSPARAM"
    assert tag_id_to_string(0x5010) == "FLAG_LUA"
    assert tag_id_to_string(0x5011) == "FLAG_INSTALL"

    # TAG_TYPE_STRINGREF
    assert tag_id_to_string(0x6000) == "InvalidTag"
    assert tag_id_to_string(0x6001) == "NAME"
    assert tag_id_to_string(0x6002) == "DESCRIPTION"
    assert tag_id_to_string(0x6003) == "MODULE"
    assert tag_id_to_string(0x6004) == "API"
    assert tag_id_to_string(0x6005) == "VENDOR"
    assert tag_id_to_string(0x6017) == "16BIT_DESCRIPTION"
    assert tag_id_to_string(0x6020) == "16BIT_MODULE_NAME"
    assert tag_id_to_string(0x6021) == "LAYER_DISPLAYNAME"

    # TAG_TYPE_LIST
    assert tag_id_to_string(0x7000) == "InvalidTag"
    assert tag_id_to_string(0x7001) == "DATABASE"
    assert tag_id_to_string(0x7002) == "LIBRARY"
    assert tag_id_to_string(0x7003) == "INEXCLUDE"
    assert tag_id_to_string(0x7004) == "SHIM"
    assert tag_id_to_string(0x7801) == "STRINGTABLE"
    assert tag_id_to_string(0x7802) == "INDEXES"
    assert tag_id_to_string(0x7803) == "INDEX"

    # TAG_TYPE_STRING
    assert tag_id_to_string(0x8000) == "InvalidTag"
    assert tag_id_to_string(0x8801) == "STRINGTABLE_ITEM"

    # TAG_TYPE_BINARY
    assert tag_id_to_string(0x9000) == "InvalidTag"
    assert tag_id_to_string(0x9002) == "PATCH_BITS"
    assert tag_id_to_string(0x9003) == "FILE_BITS"
    assert tag_id_to_string(0x9004) == "EXE_ID"
    assert tag_id_to_string(0x9801) == "INDEX_BITS"
