"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the pure-Python file-attribute layer edge cases.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

import struct
from types import SimpleNamespace

from sdbtool.apphelp import fileattr as fa
from sdbtool.apphelp.fileattr import (
    AttrInfo,
    ATTRIBUTE_AVAILABLE,
    format_attribute,
    get_file_attributes,
)


def _attr(attrs, tag):
    return next(a for a in attrs if a.tag == tag)


def test_module_type():
    assert fa._module_type(b"") == fa._MODTYPE_NONE
    assert fa._module_type(b"MZ") == fa._MODTYPE_DOS  # too short for a header
    dos = bytearray(0x40)
    dos[0:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x10000)  # e_lfanew past the end
    assert fa._module_type(bytes(dos)) == fa._MODTYPE_DOS
    ne = bytearray(0x60)
    ne[0:2] = b"MZ"
    struct.pack_into("<I", ne, 0x3C, 0x40)
    ne[0x40:0x42] = b"NE"
    assert fa._module_type(bytes(ne)) == fa._MODTYPE_NE
    junk = bytearray(0x60)
    junk[0:2] = b"MZ"
    struct.pack_into("<I", junk, 0x3C, 0x40)
    junk[0x40:0x44] = b"ZZZZ"
    assert fa._module_type(bytes(junk)) == fa._MODTYPE_DOS


def test_calculate_file_checksum():
    assert fa._calculate_file_checksum(b"") == 0  # size < 4
    assert fa._calculate_file_checksum(b"\x00" * 0x1000) == 0  # last-0x1000 branch
    assert fa._calculate_file_checksum(b"\x00" * 0x1200) == 0  # offset-0x200 branch


def test_crc_checksum():
    assert fa._crc_checksum(b"") == 0
    # > 0x2000 exercises the head+tail sampling branch
    assert isinstance(fa._crc_checksum(b"\x01" * 0x2001), int)


def test_decode_passthrough():
    assert fa._decode("already-str") == "already-str"
    assert fa._decode(b"bytes") == "bytes"


def test_export_name_helper():
    assert fa._export_name(SimpleNamespace()) is None  # no export dir
    pe = SimpleNamespace(
        DIRECTORY_ENTRY_EXPORT=SimpleNamespace(struct=SimpleNamespace(Name=0))
    )
    assert fa._export_name(pe) is None  # name rva 0
    pe = SimpleNamespace(
        DIRECTORY_ENTRY_EXPORT=SimpleNamespace(struct=SimpleNamespace(Name=0x10)),
        get_string_at_rva=lambda rva: b"",
    )
    assert fa._export_name(pe) is None  # empty name
    pe = SimpleNamespace(
        DIRECTORY_ENTRY_EXPORT=SimpleNamespace(struct=SimpleNamespace(Name=0x10)),
        get_string_at_rva=lambda rva: b"mylib.dll",
    )
    assert fa._export_name(pe) == "mylib.dll"


def test_version_resource_helper():
    ff = object()
    var_no_trans = SimpleNamespace(Key=b"VarFileInfo", Var=[SimpleNamespace(entry={})])
    var = SimpleNamespace(
        Key=b"VarFileInfo",
        Var=[
            SimpleNamespace(entry={b"Translation": "0x0409 0x04b0"}),
            SimpleNamespace(entry={b"Translation": "0x0413 0x04b0"}),
        ],
    )
    strings = SimpleNamespace(
        Key=b"StringFileInfo",
        StringTable=[SimpleNamespace(entries={b"CompanyName": b"ACME"})],
    )
    pe = SimpleNamespace(VS_FIXEDFILEINFO=[ff], FileInfo=[[var_no_trans, var, strings]])
    fixed, sd, lang = fa._version_resource(pe)
    assert fixed is ff
    assert sd == {"CompanyName": "ACME"}
    assert lang == 0x0409  # first translation wins

    empty = SimpleNamespace(VS_FIXEDFILEINFO=[], FileInfo=None)
    assert fa._version_resource(empty) == (None, {}, None)


def test_format_value_branches():
    def fmt(tag, value):
        return format_attribute(AttrInfo(tag, ATTRIBUTE_AVAILABLE, value))

    assert fmt(fa.TAG_SIZE, 2048) == 'SIZE="2048"'
    assert fmt(fa.TAG_BIN_FILE_VERSION, 0x0001000200030004) == 'BIN_FILE_VERSION="1.2.3.4"'
    assert fmt(fa.TAG_LINK_DATE, 0) == 'LINK_DATE="01/01/1970 00:00:00"'
    assert fmt(fa.TAG_VER_LANGUAGE, 0xFFFF) == 'VER_LANGUAGE="Language Neutral [0xffff]"'
    assert fmt(fa.TAG_VER_LANGUAGE, 0x0409) == 'VER_LANGUAGE="English (United States) [0x409]"'
    assert fmt(fa.TAG_VER_LANGUAGE, 0x0999) == 'VER_LANGUAGE="Language Neutral [0x999]"'
    assert fmt(fa.TAG_MODULE_TYPE, 3) == 'MODULE_TYPE="WIN32"'
    assert fmt(fa.TAG_MODULE_TYPE, 99) == 'MODULE_TYPE="NONE"'
    assert fmt(fa.TAG_PRODUCT_NAME, "Name") == 'PRODUCT_NAME="Name"'
    assert fmt(fa.TAG_CHECKSUM, 0xABCD) == 'CHECKSUM="0xABCD"'


def test_get_file_attributes_empty(tmp_path):
    f = tmp_path / "empty.bin"
    f.write_bytes(b"")
    attrs = get_file_attributes(f)
    assert _attr(attrs, fa.TAG_SIZE).value == 0
    assert not (_attr(attrs, fa.TAG_CHECKSUM).flags & ATTRIBUTE_AVAILABLE)
    assert _attr(attrs, fa.TAG_CRC_CHECKSUM).value == 0
    assert not (_attr(attrs, fa.TAG_MODULE_TYPE).flags & ATTRIBUTE_AVAILABLE)
    assert not (_attr(attrs, fa.TAG_VER_LANGUAGE).flags & ATTRIBUTE_AVAILABLE)


def test_get_file_attributes_dos(tmp_path):
    data = bytearray(0x100)
    data[0:2] = b"MZ"
    f = tmp_path / "stub.exe"
    f.write_bytes(bytes(data))
    attrs = get_file_attributes(f)
    mt = _attr(attrs, fa.TAG_MODULE_TYPE)
    assert mt.flags & ATTRIBUTE_AVAILABLE and mt.value == fa._MODTYPE_DOS
    assert _attr(attrs, fa.TAG_CHECKSUM).flags & ATTRIBUTE_AVAILABLE


def test_get_file_attributes_bad_pe(tmp_path):
    # Looks like a PE (MZ + PE signature) but is not parseable -> pefile fails.
    data = bytearray(0x44)
    data[0:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x40)
    data[0x40:0x44] = b"PE\x00\x00"
    f = tmp_path / "broken.exe"
    f.write_bytes(bytes(data))
    attrs = get_file_attributes(f)
    assert not (_attr(attrs, fa.TAG_SIZE_OF_IMAGE).flags & ATTRIBUTE_AVAILABLE)
    assert not (_attr(attrs, fa.TAG_PE_CHECKSUM).flags & ATTRIBUTE_AVAILABLE)
