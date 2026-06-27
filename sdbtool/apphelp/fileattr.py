"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Pure-Python re-implementation of the apphelp file-attribute API.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>

Reproduces the attributes returned by the (Windows) apphelp.dll
SdbGetFileAttributes / SdbFormatAttribute pair, removing the native dependency.
Based on ReactOS' sdbfileattr.c plus the additional attributes and formatting
that modern Windows apphelp.dll produces. PE parsing uses the pefile package.
"""

from __future__ import annotations

import binascii
import os
from datetime import datetime, timezone

import pefile

from sdbtool.apphelp.tags.Win10 import tag_id_to_string

ATTRIBUTE_AVAILABLE = 0x1
ATTRIBUTE_FAILED = 0x2

# Tag ids (see sdbtagid.h / tags/Win10.py)
TAG_SIZE = 0x4001
TAG_CHECKSUM = 0x4003
TAG_MODULE_TYPE = 0x4006
TAG_VERDATEHI = 0x4007
TAG_VERDATELO = 0x4008
TAG_VERFILEOS = 0x4009
TAG_VERFILETYPE = 0x400A
TAG_PE_CHECKSUM = 0x400B
TAG_VER_LANGUAGE = 0x4012
TAG_LINKER_VERSION = 0x401C
TAG_LINK_DATE = 0x401D
TAG_UPTO_LINK_DATE = 0x401E
TAG_EXE_WRAPPER = 0x4031
TAG_FROM_LINK_DATE = 0x4033
TAG_SIZE_OF_IMAGE = 0x4043
TAG_CRC_CHECKSUM = 0x404A

TAG_BIN_FILE_VERSION = 0x5002
TAG_BIN_PRODUCT_VERSION = 0x5003
TAG_UPTO_BIN_PRODUCT_VERSION = 0x5006
TAG_UPTO_BIN_FILE_VERSION = 0x500D
TAG_FROM_BIN_PRODUCT_VERSION = 0x5012
TAG_FROM_BIN_FILE_VERSION = 0x5013
TAG_FILESIZE = 0x5020

TAG_COMPANY_NAME = 0x6009
TAG_PRODUCT_NAME = 0x6010
TAG_PRODUCT_VERSION = 0x6011
TAG_FILE_DESCRIPTION = 0x6012
TAG_FILE_VERSION = 0x6013
TAG_ORIGINAL_FILENAME = 0x6014
TAG_INTERNAL_NAME = 0x6015
TAG_LEGAL_COPYRIGHT = 0x6016
TAG_16BIT_DESCRIPTION = 0x6017
TAG_16BIT_MODULE_NAME = 0x6020
TAG_EXPORT_NAME = 0x6024
TAG_UPTO_PRODUCT_VERSION = 0x6044
TAG_UPTO_FILE_VERSION = 0x6045
TAG_FROM_PRODUCT_VERSION = 0x6046
TAG_FROM_FILE_VERSION = 0x6047

# Module types (matches SdbFormatAttribute output)
_MODTYPE_NONE = 0
_MODTYPE_DOS = 1
_MODTYPE_NE = 2
_MODTYPE_PE = 3
_MODTYPE_NAMES = {0: "NONE", 1: "DOS", 2: "WIN16", 3: "WIN32"}

# Tags whose value is formatted in a special way by SdbFormatAttribute.
_VERSION_TAGS = frozenset(
    {
        TAG_BIN_FILE_VERSION,
        TAG_BIN_PRODUCT_VERSION,
        TAG_UPTO_BIN_PRODUCT_VERSION,
        TAG_UPTO_BIN_FILE_VERSION,
        TAG_FROM_BIN_PRODUCT_VERSION,
        TAG_FROM_BIN_FILE_VERSION,
    }
)
_DATE_TAGS = frozenset({TAG_LINK_DATE, TAG_UPTO_LINK_DATE, TAG_FROM_LINK_DATE})
_DECIMAL_TAGS = frozenset({TAG_SIZE, TAG_FILESIZE})

# Language ids that apphelp reports as "Language Neutral".
_NEUTRAL_LANGS = {0x0000, 0xFFFF}


class AttrInfo:
    """A single file attribute (mirrors the native ATTRINFO structure)."""

    __slots__ = ("tag", "flags", "value")

    def __init__(self, tag: int, flags: int, value=None):
        self.tag = tag
        self.flags = flags
        self.value = value


def _available(tag: int, value) -> AttrInfo:
    return AttrInfo(tag, ATTRIBUTE_AVAILABLE, value)


def _failed(tag: int) -> AttrInfo:
    return AttrInfo(tag, ATTRIBUTE_FAILED, None)


def _u32(data: bytes, off: int) -> int:
    return int.from_bytes(data[off : off + 4], "little")


def _calculate_file_checksum(data: bytes) -> int:
    """Port of apphelp's SdbpCalculateFileChecksum (a rolling 32-bit checksum)."""
    size = len(data)
    if size < 4:
        return 0
    if size >= 0x1000:
        sz = 0x1000
        off = (size - 0x1000) if size < 0x1200 else 0x200
    else:
        off = 0
        sz = size
    checks = 0
    for n in range(sz // 4):
        checks = (checks + _u32(data, off + n * 4)) & 0xFFFFFFFF
        carry = 0x80000000 if (checks & 1) else 0
        checks = (checks >> 1) | carry
    return checks


def _crc_checksum(data: bytes) -> int:
    """Port of apphelp's CRC_CHECKSUM: a zlib CRC-32 over a head+tail sample.

    The file is sampled into a 0x2000-byte buffer: the first min(size, 0x2000)
    bytes, with the upper half overwritten by the last 0x1000 bytes when the
    file is larger than 0x2000. The CRC covers 0x1000 bytes for files up to
    0x1000 bytes, otherwise 0x2000 bytes (zero-padded).
    """
    size = len(data)
    if size == 0:
        return 0
    buf = bytearray(0x2000)
    n1 = min(size, 0x2000)
    buf[0:n1] = data[0:n1]
    if size > 0x2000:
        buf[0x1000:0x2000] = data[size - 0x1000 : size]
    clen = 0x1000 if size <= 0x1000 else 0x2000
    return binascii.crc32(bytes(buf[0:clen])) & 0xFFFFFFFF


def _module_type(data: bytes) -> int:
    """Port of apphelp's SdbpGetModuleType (DOS / NE / PE detection)."""
    if len(data) < 2 or data[0:2] != b"MZ":
        return _MODTYPE_NONE
    if len(data) < 0x40:
        return _MODTYPE_DOS
    e_lfanew = _u32(data, 0x3C)
    if len(data) < e_lfanew + 2:
        return _MODTYPE_DOS
    sig2 = data[e_lfanew : e_lfanew + 2]
    if sig2 in (b"NE", b"LE"):
        return _MODTYPE_NE
    if len(data) >= e_lfanew + 4 and data[e_lfanew : e_lfanew + 4] == b"PE\x00\x00":
        return _MODTYPE_PE
    return _MODTYPE_DOS


def _decode(value) -> str:
    if isinstance(value, bytes):
        return value.decode("latin-1", "replace")
    return value


def _version_resource(pe: "pefile.PE"):
    """Return (fixed_info, strings_dict, language) or (None, {}, None)."""
    fixed = None
    if getattr(pe, "VS_FIXEDFILEINFO", None):
        fixed = pe.VS_FIXEDFILEINFO[0]

    language = None
    strings: dict[str, str] = {}
    for fileinfo in getattr(pe, "FileInfo", []) or []:
        for entry in fileinfo:
            if getattr(entry, "Key", None) == b"VarFileInfo" and hasattr(entry, "Var"):
                for var in entry.Var:
                    trans = getattr(var, "entry", {}).get(b"Translation")
                    if trans and language is None:
                        language = int(trans.split()[0], 16) & 0xFFFF
            if getattr(entry, "Key", None) == b"StringFileInfo" and hasattr(
                entry, "StringTable"
            ):
                for st in entry.StringTable:
                    for key, val in st.entries.items():
                        strings[_decode(key)] = _decode(val)
    return fixed, strings, language


def get_file_attributes(path: str | os.PathLike) -> list[AttrInfo]:
    """Return the list of file attributes for ``path`` (mirrors SdbGetFileAttributes)."""
    with open(os.fspath(path), "rb") as fp:
        data = fp.read()

    size = len(data)
    module_type = _module_type(data)

    attrs: list[AttrInfo] = []

    # Always-available, file-level attributes.
    attrs.append(_available(TAG_SIZE, size))
    attrs.append(_available(TAG_FILESIZE, size))

    pe = None
    if module_type == _MODTYPE_PE:
        try:
            pe = pefile.PE(data=data, fast_load=False)
        except pefile.PEFormatError:
            pe = None

    if pe is not None:
        attrs.append(_available(TAG_SIZE_OF_IMAGE, pe.OPTIONAL_HEADER.SizeOfImage))
    else:
        attrs.append(_failed(TAG_SIZE_OF_IMAGE))

    if size:
        attrs.append(_available(TAG_CHECKSUM, _calculate_file_checksum(data)))
    else:
        attrs.append(_failed(TAG_CHECKSUM))

    fixed, strings, language = (None, {}, None)
    if pe is not None:
        fixed, strings, language = _version_resource(pe)

    def bin_version(ms: int, ls: int) -> int:
        return ((ms & 0xFFFFFFFF) << 32) | (ls & 0xFFFFFFFF)

    if fixed is not None:
        file_ver = bin_version(fixed.FileVersionMS, fixed.FileVersionLS)
        prod_ver = bin_version(fixed.ProductVersionMS, fixed.ProductVersionLS)
    else:
        file_ver = prod_ver = None

    def ver_attr(tag: int, value):
        return _available(tag, value) if value is not None else _failed(tag)

    def str_attr(tag: int, key: str):
        val = strings.get(key)
        return _available(tag, val) if val is not None else _failed(tag)

    attrs.append(ver_attr(TAG_BIN_FILE_VERSION, file_ver))
    attrs.append(ver_attr(TAG_BIN_PRODUCT_VERSION, prod_ver))
    attrs.append(str_attr(TAG_PRODUCT_VERSION, "ProductVersion"))
    attrs.append(str_attr(TAG_FILE_DESCRIPTION, "FileDescription"))
    attrs.append(str_attr(TAG_COMPANY_NAME, "CompanyName"))
    attrs.append(str_attr(TAG_PRODUCT_NAME, "ProductName"))
    attrs.append(str_attr(TAG_FILE_VERSION, "FileVersion"))
    attrs.append(str_attr(TAG_ORIGINAL_FILENAME, "OriginalFilename"))
    attrs.append(str_attr(TAG_INTERNAL_NAME, "InternalName"))
    attrs.append(str_attr(TAG_LEGAL_COPYRIGHT, "LegalCopyright"))

    if fixed is not None:
        attrs.append(_available(TAG_VERDATEHI, fixed.FileDateMS))
        attrs.append(_available(TAG_VERDATELO, fixed.FileDateLS))
        attrs.append(_available(TAG_VERFILEOS, fixed.FileOS))
        attrs.append(_available(TAG_VERFILETYPE, fixed.FileType))
    else:
        attrs.append(_failed(TAG_VERDATEHI))
        attrs.append(_failed(TAG_VERDATELO))
        attrs.append(_failed(TAG_VERFILEOS))
        attrs.append(_failed(TAG_VERFILETYPE))

    if module_type != _MODTYPE_NONE:
        attrs.append(_available(TAG_MODULE_TYPE, module_type))
    else:
        attrs.append(_failed(TAG_MODULE_TYPE))

    if pe is not None:
        oh = pe.OPTIONAL_HEADER
        fh = pe.FILE_HEADER
        attrs.append(_available(TAG_PE_CHECKSUM, oh.CheckSum))
        attrs.append(
            _available(
                TAG_LINKER_VERSION,
                ((oh.MajorImageVersion & 0xFFFF) << 16)
                | (oh.MinorImageVersion & 0xFFFF),
            )
        )
    else:
        attrs.append(_failed(TAG_PE_CHECKSUM))
        attrs.append(_failed(TAG_LINKER_VERSION))

    # 16-bit (NE) only.
    attrs.append(_failed(TAG_16BIT_DESCRIPTION))
    attrs.append(_failed(TAG_16BIT_MODULE_NAME))

    attrs.append(ver_attr(TAG_FROM_BIN_FILE_VERSION, file_ver))
    attrs.append(ver_attr(TAG_FROM_BIN_PRODUCT_VERSION, prod_ver))
    attrs.append(ver_attr(TAG_UPTO_BIN_FILE_VERSION, file_ver))
    attrs.append(ver_attr(TAG_UPTO_BIN_PRODUCT_VERSION, prod_ver))

    if pe is not None:
        timestamp = pe.FILE_HEADER.TimeDateStamp
        attrs.append(_available(TAG_LINK_DATE, timestamp))
        attrs.append(_available(TAG_FROM_LINK_DATE, timestamp))
        attrs.append(_available(TAG_UPTO_LINK_DATE, timestamp))
    else:
        attrs.append(_failed(TAG_LINK_DATE))
        attrs.append(_failed(TAG_FROM_LINK_DATE))
        attrs.append(_failed(TAG_UPTO_LINK_DATE))

    export_name = None
    if pe is not None and hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        name = getattr(pe.DIRECTORY_ENTRY_EXPORT.struct, "Name", 0)
        raw = pe.get_string_at_rva(name) if name else None
        if raw:
            export_name = _decode(raw)
    attrs.append(
        _available(TAG_EXPORT_NAME, export_name)
        if export_name is not None
        else _failed(TAG_EXPORT_NAME)
    )

    if pe is not None and language is not None:
        attrs.append(_available(TAG_VER_LANGUAGE, language))
    else:
        attrs.append(_failed(TAG_VER_LANGUAGE))

    if pe is not None:
        attrs.append(_available(TAG_EXE_WRAPPER, 0))
    else:
        attrs.append(_failed(TAG_EXE_WRAPPER))

    attrs.append(_available(TAG_CRC_CHECKSUM, _crc_checksum(data)))

    attrs.append(str_attr(TAG_FROM_PRODUCT_VERSION, "ProductVersion"))
    attrs.append(str_attr(TAG_UPTO_PRODUCT_VERSION, "ProductVersion"))
    attrs.append(str_attr(TAG_FROM_FILE_VERSION, "FileVersion"))
    attrs.append(str_attr(TAG_UPTO_FILE_VERSION, "FileVersion"))

    return attrs


def _format_language(value: int) -> str:
    if value in _NEUTRAL_LANGS:
        name = "Language Neutral"
    else:
        name = _LANGUAGE_NAMES.get(value, "Language Neutral")
    return f"{name} [{value:#x}]"


def _format_value(tag: int, value) -> str:
    if tag in _DECIMAL_TAGS:
        return str(value)
    if tag in _VERSION_TAGS:
        return "%d.%d.%d.%d" % (
            (value >> 48) & 0xFFFF,
            (value >> 32) & 0xFFFF,
            (value >> 16) & 0xFFFF,
            value & 0xFFFF,
        )
    if tag in _DATE_TAGS:
        dt = datetime.fromtimestamp(value, tz=timezone.utc)
        return dt.strftime("%m/%d/%Y %H:%M:%S")
    if tag == TAG_VER_LANGUAGE:
        return _format_language(value)
    if tag == TAG_MODULE_TYPE:
        return _MODTYPE_NAMES.get(value, "NONE")
    if isinstance(value, str):
        return value
    return f"0x{value:X}"


def format_attribute(attr: AttrInfo) -> str:
    """Format an attribute as ``NAME="value"`` (mirrors SdbFormatAttribute)."""
    if not (attr.flags & ATTRIBUTE_AVAILABLE):
        name = tag_id_to_string(attr.tag)
        raise ValueError(f"Failed to format attribute ({name})")
    name = tag_id_to_string(attr.tag)
    return f'{name}="{_format_value(attr.tag, attr.value)}"'


# A subset of the Windows language-name table. apphelp formats the LANGID using
# the OS language list; common entries are reproduced here, with everything else
# (and the neutral ids) reported as "Language Neutral".
_LANGUAGE_NAMES = {
    0x0409: "English (United States)",
    0x0809: "English (United Kingdom)",
    0x0413: "Dutch (Netherlands)",
    0x0407: "German (Germany)",
    0x040C: "French (France)",
    0x0410: "Italian (Italy)",
    0x040A: "Spanish (Spain)",
    0x0419: "Russian (Russia)",
    0x0411: "Japanese (Japan)",
    0x0804: "Chinese (Simplified, China)",
}
