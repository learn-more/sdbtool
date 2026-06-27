"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Pure-Python reader for SDB (shim database) files.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>

This is a pure-Python port of the SDB reading functions from the ReactOS
apphelp module (sdbread.c / sdbapi.c), removing the dependency on the native
apphelp.dll. The function names and semantics mirror the original Win32 API.
"""

from __future__ import annotations

# Tag type nibble (high 4 bits of a TAG)
TAG_TYPE_MASK = 0xF000
TAG_TYPE_NULL = 0x1000
TAG_TYPE_BYTE = 0x2000
TAG_TYPE_WORD = 0x3000
TAG_TYPE_DWORD = 0x4000
TAG_TYPE_QWORD = 0x5000
TAG_TYPE_STRINGREF = 0x6000
TAG_TYPE_LIST = 0x7000
TAG_TYPE_STRING = 0x8000
TAG_TYPE_BINARY = 0x9000

TAG_NULL = 0x0
TAGID_NULL = 0x0
TAGID_ROOT = 0x0
_TAGID_ROOT = 12  # First tag follows the 12-byte header

_SIZEOF_TAG = 2
_SIZEOF_DWORD = 4

# Tags needed to resolve the string table and the database name / id.
_TAG_NAME = 0x6001
_TAG_DATABASE = 0x7001
_TAG_STRINGTABLE = 0x7801
_TAG_DATABASE_ID = 0x9007

# Fixed sizes for the data types with a fixed size, indexed by (type >> 12) - 1.
_FIXED_SIZES = (0, 1, 2, 4, 8, 4)  # NULL, BYTE, WORD, DWORD, QWORD, STRINGREF


class SdbFile:
    """An opened shim database, holding the raw bytes and cached metadata.

    Instances are returned by :func:`SdbOpenDatabase` and act as the opaque
    handle (``PDB``) that the rest of the reading API operates on.
    """

    def __init__(self, data: bytes, major: int, minor: int):
        self.data = data
        self.size = len(data)
        self.major = major
        self.minor = minor
        self.stringtable: int = TAGID_NULL
        self.database_id: bytes | None = None
        self.database_name: str | None = None


def SdbpReadData(pdb: SdbFile, offset: int, num: int) -> bytes | None:
    """Read ``num`` bytes at ``offset``, or ``None`` on overflow / out of bounds."""
    end = offset + num
    # Either overflow or no data to read
    if end <= offset:
        return None
    if pdb.size < end:
        return None
    return pdb.data[offset:end]


def _read_uint(pdb: SdbFile, offset: int, num: int) -> int | None:
    raw = SdbpReadData(pdb, offset, num)
    if raw is None:
        return None
    return int.from_bytes(raw, "little")


def SdbGetTagFromTagID(pdb: SdbFile, tagid: int) -> int:
    """Return the TAG stored at ``tagid``, or :data:`TAG_NULL` on failure."""
    value = _read_uint(pdb, tagid, _SIZEOF_TAG)
    return TAG_NULL if value is None else value


def SdbGetTagDataSize(pdb: SdbFile, tagid: int) -> int:
    """Return the size in bytes of the data stored at ``tagid``."""
    ttype = SdbGetTagFromTagID(pdb, tagid) & TAG_TYPE_MASK
    if ttype == TAG_NULL:
        return 0

    if ttype <= TAG_TYPE_STRINGREF:
        return _FIXED_SIZES[(ttype >> 12) - 1]

    # Dynamically-sized tag (list / string / binary): the size follows the tag.
    size = _read_uint(pdb, tagid + _SIZEOF_TAG, _SIZEOF_DWORD)
    return 0 if size is None else size


def _sdbp_get_tag_size(pdb: SdbFile, tagid: int) -> int:
    """Total on-disk size of the tag at ``tagid`` (tag header + data).

    Tag data is padded to a 2-byte (WORD) boundary on disk, so e.g. a BYTE tag
    occupies a 2-byte data slot (the trailing pad byte is uninitialized). This
    rounding is required to correctly walk databases written by apphelp.
    """
    ttype = SdbGetTagFromTagID(pdb, tagid) & TAG_TYPE_MASK
    if ttype == TAG_NULL:
        return 0

    size = (SdbGetTagDataSize(pdb, tagid) + 1) & ~1
    if ttype <= TAG_TYPE_STRINGREF:
        return size + _SIZEOF_TAG
    return size + _SIZEOF_TAG + _SIZEOF_DWORD


def SdbGetFirstChild(pdb: SdbFile, parent: int) -> int:
    """Return the TAGID of the first child of ``parent`` (or :data:`TAGID_NULL`)."""
    if parent == TAGID_ROOT:
        # header-only database: no tags
        if pdb.size <= _TAGID_ROOT:
            return TAGID_NULL
        return _TAGID_ROOT

    # Only list tags can have children.
    if (SdbGetTagFromTagID(pdb, parent) & TAG_TYPE_MASK) != TAG_TYPE_LIST:
        return TAGID_NULL

    # An empty list has no children. (Native Windows apphelp.dll returns NULL
    # here; ReactOS' sdbread.c omits this check and relies on the caller.)
    if SdbGetTagDataSize(pdb, parent) == 0:
        return TAGID_NULL

    return parent + _SIZEOF_TAG + _SIZEOF_DWORD


def SdbGetNextChild(pdb: SdbFile, parent: int, prev_child: int) -> int:
    """Return the TAGID of the child after ``prev_child`` (or :data:`TAGID_NULL`)."""
    prev_child_size = _sdbp_get_tag_size(pdb, prev_child)
    if prev_child_size == 0:
        return TAGID_NULL

    next_child = prev_child + prev_child_size
    if next_child >= pdb.size:
        return TAGID_NULL

    if parent == TAGID_ROOT:
        return next_child

    parent_size = _sdbp_get_tag_size(pdb, parent)
    if parent_size == 0:
        return TAGID_NULL

    # Specified parent has no more children
    if next_child >= parent + parent_size:
        return TAGID_NULL

    return next_child


def SdbFindFirstTag(pdb: SdbFile, parent: int, tag: int) -> int:
    """Return the TAGID of the first child of ``parent`` whose TAG equals ``tag``."""
    it = SdbGetFirstChild(pdb, parent)
    while it != TAGID_NULL:
        if SdbGetTagFromTagID(pdb, it) == tag:
            return it
        it = SdbGetNextChild(pdb, parent, it)
    return TAGID_NULL


def _check_type(pdb: SdbFile, tagid: int, ttype: int) -> bool:
    tag = SdbGetTagFromTagID(pdb, tagid)
    if tag == TAG_NULL:
        return False
    return (tag & TAG_TYPE_MASK) == ttype


def SdbReadBYTETag(pdb: SdbFile, tagid: int, default: int = 0) -> int:
    if _check_type(pdb, tagid, TAG_TYPE_BYTE):
        value = _read_uint(pdb, tagid + _SIZEOF_TAG, 1)
        if value is not None:
            return value
    return default


def SdbReadWORDTag(pdb: SdbFile, tagid: int, default: int = 0) -> int:
    if _check_type(pdb, tagid, TAG_TYPE_WORD):
        value = _read_uint(pdb, tagid + _SIZEOF_TAG, 2)
        if value is not None:
            return value
    return default


def SdbReadDWORDTag(pdb: SdbFile, tagid: int, default: int = 0) -> int:
    if _check_type(pdb, tagid, TAG_TYPE_DWORD):
        value = _read_uint(pdb, tagid + _SIZEOF_TAG, 4)
        if value is not None:
            return value
    return default


def SdbReadQWORDTag(pdb: SdbFile, tagid: int, default: int = 0) -> int:
    if _check_type(pdb, tagid, TAG_TYPE_QWORD):
        value = _read_uint(pdb, tagid + _SIZEOF_TAG, 8)
        if value is not None:
            return value
    return default


def SdbReadBinaryTag(pdb: SdbFile, tagid: int) -> bytes:
    """Return the raw bytes of a binary tag (empty bytes for an empty tag)."""
    if not _check_type(pdb, tagid, TAG_TYPE_BINARY):
        raise ValueError(f"Tag 0x{tagid:x} is not a binary tag")
    data_size = _read_uint(pdb, tagid + _SIZEOF_TAG, _SIZEOF_DWORD)
    if data_size is None:
        raise ValueError(f"Failed to read binary tag 0x{tagid:x}")
    if data_size == 0:
        return b""
    raw = SdbpReadData(pdb, tagid + _SIZEOF_TAG + _SIZEOF_DWORD, data_size)
    if raw is None:
        raise ValueError(f"Failed to read binary tag 0x{tagid:x}")
    return raw


def SdbGetStringTagPtr(pdb: SdbFile, tagid: int) -> str | None:
    """Return the string for a STRING / STRINGREF tag, or ``None`` on failure."""
    tag = SdbGetTagFromTagID(pdb, tagid)
    if tag == TAG_NULL:
        return None

    ttype = tag & TAG_TYPE_MASK
    if ttype == TAG_TYPE_STRINGREF:
        # No string table: all references are invalid.
        if pdb.stringtable == TAGID_NULL:
            return None
        # A STRINGREF stores the offset of the string relative to the table.
        stored = _read_uint(pdb, tagid + _SIZEOF_TAG, _SIZEOF_DWORD)
        if stored is None:
            return None
        offset = pdb.stringtable + stored + _SIZEOF_TAG + _SIZEOF_DWORD
    elif ttype == TAG_TYPE_STRING:
        offset = tagid + _SIZEOF_TAG + _SIZEOF_DWORD
    else:
        return None

    # The byte size (including the terminating NUL) precedes the string data.
    size = _read_uint(pdb, offset - _SIZEOF_DWORD, _SIZEOF_DWORD)
    if size is None:
        return None
    raw = SdbpReadData(pdb, offset, size)
    if raw is None:
        return None
    try:
        return raw.decode("utf-16-le").rstrip("\x00")
    except UnicodeDecodeError:
        # Corrupt / malformed string data: treat as a read failure.
        return None


def _resolve_metadata(pdb: SdbFile) -> None:
    """Cache the string table offset, database id and name (as done on open)."""
    pdb.stringtable = SdbFindFirstTag(pdb, TAGID_ROOT, _TAG_STRINGTABLE)

    root = SdbFindFirstTag(pdb, TAGID_ROOT, _TAG_DATABASE)
    if root != TAGID_NULL:
        id_tag = SdbFindFirstTag(pdb, root, _TAG_DATABASE_ID)
        if id_tag != TAGID_NULL:
            try:
                data = SdbReadBinaryTag(pdb, id_tag)
            except ValueError:
                data = b""
            if len(data) == 16:
                pdb.database_id = data
        name_tag = SdbFindFirstTag(pdb, root, _TAG_NAME)
        if name_tag != TAGID_NULL:
            pdb.database_name = SdbGetStringTagPtr(pdb, name_tag)


def SdbOpenDatabase(path: str) -> SdbFile | None:
    """Open and validate a shim database file. Returns ``None`` on failure."""
    try:
        with open(path, "rb") as fp:
            data = fp.read()
    except OSError:
        return None

    if len(data) < 12 or data[8:12] != b"sdbf":
        return None

    major = int.from_bytes(data[0:4], "little")
    minor = int.from_bytes(data[4:8], "little")
    if major not in (2, 3):
        return None

    pdb = SdbFile(data, major, minor)
    _resolve_metadata(pdb)
    return pdb
