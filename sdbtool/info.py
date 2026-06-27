"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Read high-level information about an SDB file.
COPYRIGHT:   Copyright 2025,2026 Mark Jansen <mark.jansen@reactos.org>
"""

import os
from dataclasses import dataclass
from uuid import UUID
from sdbtool.apphelp import sdb_reader

DB_INFO_FLAGS_VALID_GUID = 1
# Always set by the (Win10+) SdbGetDatabaseInformationByName implementation.
_DB_INFO_FLAGS_BASE = 0x10000000

_TAG_DATABASE = 0x7001
_TAG_RUNTIME_PLATFORM = 0x4021
_PLATFORM_MASK = 0x1F  # X86 | AMD64 | X86_ON_AMD64 | ARM | ARM64


@dataclass
class DatabaseInformation:
    """Database information structure."""

    Description: str | None
    dwMajor: int
    dwMinor: int
    dwFlags: int
    Id: UUID | None
    dwRuntimePlatform: int | None


def _runtime_platform(pdb: sdb_reader.SdbFile) -> int:
    """Reproduce the dwRuntimePlatform value reported by apphelp.dll.

    Windows derives this from the DATABASE's RUNTIME_PLATFORM tag, reporting the
    most significant platform bit (e.g. 0x25 -> 4, 0x82 -> 2), and defaults to 4
    (X86_ON_AMD64) when the tag is absent.
    """
    root = sdb_reader.SdbFindFirstTag(pdb, sdb_reader.TAGID_ROOT, _TAG_DATABASE)
    bits = 0
    if root != sdb_reader.TAGID_NULL:
        tag = sdb_reader.SdbFindFirstTag(pdb, root, _TAG_RUNTIME_PLATFORM)
        if tag != sdb_reader.TAGID_NULL:
            bits = sdb_reader.SdbReadDWORDTag(pdb, tag) & _PLATFORM_MASK
    if not bits:
        return 4
    return 1 << (bits.bit_length() - 1)


def get_info(file_name: str | os.PathLike) -> DatabaseInformation:
    pdb = sdb_reader.SdbOpenDatabase(os.fspath(file_name))
    if pdb is None:
        raise ValueError(f"Failed to get database information for '{file_name}'")

    flags = _DB_INFO_FLAGS_BASE
    id_value = None
    if pdb.database_id is not None:
        flags |= DB_INFO_FLAGS_VALID_GUID
        id_value = UUID(bytes_le=pdb.database_id)

    return DatabaseInformation(
        Description=pdb.database_name or None,
        dwMajor=pdb.major,
        dwMinor=pdb.minor,
        dwFlags=flags,
        Id=id_value,
        dwRuntimePlatform=_runtime_platform(pdb),
    )
