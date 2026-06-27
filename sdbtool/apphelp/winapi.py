"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Low-level interface for reading SDB files.
COPYRIGHT:   Copyright 2025,2026 Mark Jansen <mark.jansen@reactos.org>

This is a thin facade over the pure-Python SDB reader (sdb_reader.py). It keeps
the historical apphelp-style function names used by the high-level interface,
but no longer depends on the native apphelp.dll.
"""

from sdbtool.apphelp import sdb_reader
from sdbtool.apphelp.sdb_reader import SdbFile


def SdbOpenDatabase(path: str, path_type: int = 0) -> SdbFile | None:
    """Open a database at the specified path.

    ``path_type`` (DOS_PATH / NT_PATH) is accepted for API compatibility; the
    file is always read directly through the filesystem.
    """
    return sdb_reader.SdbOpenDatabase(path)


def SdbCloseDatabase(db: SdbFile | None) -> None:
    """Close the specified database (no-op; kept for API compatibility)."""


def SdbGetFirstChild(db: SdbFile, parent: int) -> int:
    """Get the first child tag of the specified parent."""
    return sdb_reader.SdbGetFirstChild(db, parent)


def SdbGetNextChild(db: SdbFile, parent: int, prev_child: int) -> int:
    """Get the next child tag of the specified parent."""
    return sdb_reader.SdbGetNextChild(db, parent, prev_child)


def SdbGetTagFromTagID(db: SdbFile, tag_id: int) -> int:
    """Get the tag from the specified tag ID."""
    return sdb_reader.SdbGetTagFromTagID(db, tag_id)


def SdbReadBYTETag(db: SdbFile, tag_id: int, default: int = 0) -> int:
    """Read a BYTE tag from the database."""
    return sdb_reader.SdbReadBYTETag(db, tag_id, default)


def SdbReadWORDTag(db: SdbFile, tag_id: int, default: int = 0) -> int:
    """Read a WORD tag from the database."""
    return sdb_reader.SdbReadWORDTag(db, tag_id, default)


def SdbReadDWORDTag(db: SdbFile, tag_id: int, default: int = 0) -> int:
    """Read a DWORD tag from the database."""
    return sdb_reader.SdbReadDWORDTag(db, tag_id, default)


def SdbReadQWORDTag(db: SdbFile, tag_id: int, default: int = 0) -> int:
    """Read a QWORD tag from the database."""
    return sdb_reader.SdbReadQWORDTag(db, tag_id, default)


def SdbReadBinaryTag(db: SdbFile, tag_id: int) -> bytes:
    """Read a binary tag from the database."""
    return sdb_reader.SdbReadBinaryTag(db, tag_id)


def SdbGetStringTagPtr(db: SdbFile, tag_id: int) -> str:
    """Get the string value of the specified tag."""
    value = sdb_reader.SdbGetStringTagPtr(db, tag_id)
    return value if value is not None else ""
