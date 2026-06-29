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
    is_excluded,
    normalize_tag_name,
    xml_tag_name,
)
from sdbtool.apphelp.tags import KNOWN_VERSIONS, DEFAULT_VERSION
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
    assert tag_id_to_string(0x1000) == "InvalidTag_0x1000"
    assert tag_id_to_string(0x1001) == "INCLUDE"
    assert tag_id_to_string(0x1002) == "GENERAL"
    assert tag_id_to_string(0x1003) == "MATCH_LOGIC_NOT"
    assert tag_id_to_string(0x1004) == "APPLY_ALL_SHIMS"

    # TAG_TYPE_WORD
    assert tag_id_to_string(0x3000) == "InvalidTag_0x3000"
    assert tag_id_to_string(0x3001) == "MATCH_MODE"
    assert tag_id_to_string(0x3002) == "QUIRK_COMPONENT_CODE_ID"
    assert tag_id_to_string(0x3003) == "QUIRK_CODE_ID"
    assert tag_id_to_string(0x3801) == "TAG"
    assert tag_id_to_string(0x3802) == "INDEX_TAG"
    assert tag_id_to_string(0x3803) == "INDEX_KEY"

    # TAG_TYPE_DWORD
    assert tag_id_to_string(0x4000) == "InvalidTag_0x4000"
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
    assert tag_id_to_string(0x5000) == "InvalidTag_0x5000"
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
    assert tag_id_to_string(0x6000) == "InvalidTag_0x6000"
    assert tag_id_to_string(0x6001) == "NAME"
    assert tag_id_to_string(0x6002) == "DESCRIPTION"
    assert tag_id_to_string(0x6003) == "MODULE"
    assert tag_id_to_string(0x6004) == "API"
    assert tag_id_to_string(0x6005) == "VENDOR"
    assert tag_id_to_string(0x6017) == "16BIT_DESCRIPTION"
    assert tag_id_to_string(0x6020) == "16BIT_MODULE_NAME"
    assert tag_id_to_string(0x6021) == "LAYER_DISPLAYNAME"

    # TAG_TYPE_LIST
    assert tag_id_to_string(0x7000) == "InvalidTag_0x7000"
    assert tag_id_to_string(0x7001) == "DATABASE"
    assert tag_id_to_string(0x7002) == "LIBRARY"
    assert tag_id_to_string(0x7003) == "INEXCLUDE"
    assert tag_id_to_string(0x7004) == "SHIM"
    assert tag_id_to_string(0x7801) == "STRINGTABLE"
    assert tag_id_to_string(0x7802) == "INDEXES"
    assert tag_id_to_string(0x7803) == "INDEX"

    # TAG_TYPE_STRING
    assert tag_id_to_string(0x8000) == "InvalidTag_0x8000"
    assert tag_id_to_string(0x8801) == "STRINGTABLE_ITEM"

    # TAG_TYPE_BINARY
    assert tag_id_to_string(0x9000) == "InvalidTag_0x9000"
    assert tag_id_to_string(0x9002) == "PATCH_BITS"
    assert tag_id_to_string(0x9003) == "FILE_BITS"
    assert tag_id_to_string(0x9004) == "EXE_ID"
    assert tag_id_to_string(0x9801) == "INDEX_BITS"


def test_tag_id_to_string_version_aware():
    # Sanity: the generated tables cover the versions we ship.
    assert KNOWN_VERSIONS[-1] == DEFAULT_VERSION
    assert {"0501", "0A00-26200"} <= set(KNOWN_VERSIONS)

    # OS_SKU (0x4022) exists on XP but was dropped on Win11; selecting the source
    # OS resolves it, while the newest table reports it as unknown (hex preserved).
    assert tag_id_to_string(0x4022, "0501") == "OS_SKU"
    assert tag_id_to_string(0x4022, "0A00-26200") == "InvalidTag_0x4022"
    assert tag_id_to_string(0x4022) == "InvalidTag_0x4022"

    # 0x4023 was renamed OS_PLATFORM -> GUEST_TARGET_PLATFORM.
    assert tag_id_to_string(0x4023, "0502") == "OS_PLATFORM"
    assert tag_id_to_string(0x4023, "0A00-26200") == "GUEST_TARGET_PLATFORM"

    # A modern tag is still decoded for an old target via forward fallback.
    assert tag_id_to_string(0x7050, "0501") == "FEATURE_DEF"

    # Unknown everywhere -> hex-preserving fallback; an unknown os falls back to newest.
    assert tag_id_to_string(0x1234, "bogus") == "InvalidTag_0x1234"


def test_is_excluded_matches_unknown_by_prefix():
    assert is_excluded("PATCH", {"PATCH"})
    assert is_excluded("InvalidTag_0x7000", {"InvalidTag"})
    assert not is_excluded("InvalidTag_0x7000", {"PATCH"})
    assert not is_excluded("SHIM", {"InvalidTag"})


def test_is_excluded_matches_normalized_names():
    # Exclusion given as the output (normalized) name matches the raw Windows name.
    assert is_excluded("MSI TRANSFORM", {"MSI_TRANSFORM"})  # space -> underscore
    assert is_excluded("EXE_ID(GUID)", {"EXE_ID"})  # paren stripped
    assert is_excluded("16BIT_DESCRIPTION", {"S16BIT_DESCRIPTION"})  # XML form
    # Works against a list too (sdb2xml passes a list, not a set).
    assert is_excluded("MSI TRANSFORM", ["MSI_TRANSFORM"])
    assert not is_excluded("MSI TRANSFORM", {"PATCH"})


def test_normalize_tag_name():
    # Raw Windows names from older apphelp -> identifier-ish form.
    assert normalize_tag_name("MSI TRANSFORM") == "MSI_TRANSFORM"
    assert normalize_tag_name("MSI CUSTOM ACTION") == "MSI_CUSTOM_ACTION"
    assert normalize_tag_name("EXE_ID(GUID)") == "EXE_ID"
    assert normalize_tag_name("DATABASE_ID(GUID)") == "DATABASE_ID"
    # Leading digit is left alone for JSON; clean names unchanged.
    assert normalize_tag_name("16BIT_DESCRIPTION") == "16BIT_DESCRIPTION"
    assert normalize_tag_name("SHIM") == "SHIM"


def test_xml_tag_name():
    # Same cleanup as normalize_tag_name, plus a leading-digit guard for XML.
    assert xml_tag_name("16BIT_DESCRIPTION") == "S16BIT_DESCRIPTION"
    assert xml_tag_name("16BIT_MODULE_NAME") == "S16BIT_MODULE_NAME"
    assert xml_tag_name("MSI TRANSFORM") == "MSI_TRANSFORM"
    assert xml_tag_name("EXE_ID(GUID)") == "EXE_ID"
    assert xml_tag_name("SHIM") == "SHIM"


def test_guid_comment_survives_paren_name():
    # A "(GUID)" suffix (XP/2003 raw name) must not defeat the GUID annotation.
    from sdbtool.apphelp import TagType

    class FakeBinaryTag:
        type = TagType.BINARY
        name = "EXE_ID(GUID)"

        def read_bytes(self):
            return bytes(range(16))

    value, comment = tag_value_to_string(FakeBinaryTag())
    assert comment is not None and comment.startswith("{") and comment.endswith("}")
