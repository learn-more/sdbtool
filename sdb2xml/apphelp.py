'''
PROJECT:     sdb2xml
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     interface to the AppHelp API for reading SDB files.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
'''
from ctypes import windll, c_void_p, c_uint16, c_uint32, c_wchar_p, POINTER, c_ubyte, c_uint64
from enum import IntEnum

class PathType(IntEnum):
    DOS_PATH = 0
    NT_PATH = 1


TAGID_NULL = 0x0
TAGID_ROOT = 0x0
_TAGID_ROOT = 12

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


APPHELP = windll.apphelp

# PDB WINAPI SdbOpenDatabase(LPCWSTR path, PATH_TYPE type);
APPHELP.SdbOpenDatabase.argtypes = [c_wchar_p, c_uint32]
APPHELP.SdbOpenDatabase.restype = c_void_p

# void WINAPI SdbCloseDatabase(PDB);
APPHELP.SdbCloseDatabase.argtypes = [c_void_p]

# TAGID WINAPI SdbGetFirstChild(PDB pdb, TAGID parent);
APPHELP.SdbGetFirstChild.argtypes = [c_void_p, c_uint32]
APPHELP.SdbGetFirstChild.restype = c_uint32

# TAGID WINAPI SdbGetNextChild(PDB pdb, TAGID parent, TAGID prev_child);
APPHELP.SdbGetNextChild.argtypes = [c_void_p, c_uint32, c_uint32]
APPHELP.SdbGetNextChild.restype = c_uint32

# TAG WINAPI SdbGetTagFromTagID(PDB pdb, TAGID tagid);
APPHELP.SdbGetTagFromTagID.argtypes = [c_void_p, c_uint32]
APPHELP.SdbGetTagFromTagID.restype = c_uint16

# LPCWSTR WINAPI SdbTagToString(TAG tag);
APPHELP.SdbTagToString.argtypes = [c_uint16]
APPHELP.SdbTagToString.restype = c_wchar_p

# WORD WINAPI SdbReadDWORDTag(PDB pdb, TAGID tagid, WORD ret);
APPHELP.SdbReadWORDTag.argtypes = [c_void_p, c_uint32, c_uint16]
APPHELP.SdbReadWORDTag.restype = c_uint16

# DWORD WINAPI SdbReadDWORDTag(PDB pdb, TAGID tagid, DWORD ret);
APPHELP.SdbReadDWORDTag.argtypes = [c_void_p, c_uint32, c_uint32]
APPHELP.SdbReadDWORDTag.restype = c_uint32

# QWORD WINAPI SdbReadQWORDTag(PDB pdb, TAGID tagid, QWORD ret);
APPHELP.SdbReadQWORDTag.argtypes = [c_void_p, c_uint32, c_uint64]
APPHELP.SdbReadQWORDTag.restype = c_uint64

# DWORD WINAPI SdbGetTagDataSize(PDB pdb, TAGID tagid);
APPHELP.SdbGetTagDataSize.argtypes = [c_void_p, c_uint32]
APPHELP.SdbGetTagDataSize.restype = c_uint32

# BOOL WINAPI SdbReadBinaryTag(PDB pdb, TAGID tagid, PBYTE buffer, DWORD size);
APPHELP.SdbReadBinaryTag.argtypes = [c_void_p, c_uint32, POINTER(c_ubyte), c_uint32]
APPHELP.SdbReadBinaryTag.restype = c_uint32

# LPWSTR WINAPI SdbGetStringTagPtr(PDB pdb, TAGID tagid);
APPHELP.SdbGetStringTagPtr.argtypes = [c_void_p, c_uint32]
APPHELP.SdbGetStringTagPtr.restype = c_wchar_p

def _get_tag_type(tag: int) -> int:
    """Extracts the type from a tag."""
    return tag & TAG_TYPE_MASK

def tag_to_string(tag: int) -> str:
    """Converts a tag to its string representation."""
    return APPHELP.SdbTagToString(tag)

class Tag:
    def __init__(self, db: 'SdbDatabase', tag_id: int):
        self.db = db
        self.tag_id = tag_id
        if tag_id == TAGID_ROOT:
            self.tag = TAG_NULL
            self.name = 'SDB'
            self.type = TAG_TYPE_LIST
        else:
            self.tag = APPHELP.SdbGetTagFromTagID(db.handle, tag_id)
            self.name = APPHELP.SdbTagToString(self.tag)
            self.type = _get_tag_type(self.tag)

    def tags(self):
        child = APPHELP.SdbGetFirstChild(self.db.handle, self.tag_id)
        while child != 0:
            yield Tag(self.db, child)
            child = APPHELP.SdbGetNextChild(self.db.handle, self.tag_id, child)

    def as_word(self, default: int = 0) -> int:
        """Returns the tag value as a word (16-bit integer)."""
        if self.type != TAG_TYPE_WORD:
            raise ValueError(f"Tag {self.name} is not a WORD type")
        return APPHELP.SdbReadWORDTag(self.db.handle, self.tag_id, default)

    def as_dword(self, default: int = 0) -> int:
        """Returns the tag value as a dword (32-bit integer)."""
        if self.type != TAG_TYPE_DWORD:
            raise ValueError(f"Tag {self.name} is not a DWORD type")
        return APPHELP.SdbReadDWORDTag(self.db.handle, self.tag_id, default)

    def as_qword(self, default: int = 0) -> int:
        """Returns the tag value as a qword (64-bit integer)."""
        if self.type != TAG_TYPE_QWORD:
            raise ValueError(f"Tag {self.name} is not a QWORD type")
        return APPHELP.SdbReadQWORDTag(self.db.handle, self.tag_id, default)

    def as_bytes(self) -> bytes:
        """Returns the tag value as bytes."""
        if self.type != TAG_TYPE_BINARY:
            raise ValueError(f"Tag {self.name} is not a BINARY type")
        size = APPHELP.SdbGetTagDataSize(self.db.handle, self.tag_id)
        if size == 0:
            return b''
        data = (c_ubyte * size)()
        result = APPHELP.SdbReadBinaryTag(self.db.handle, self.tag_id, data, size)
        if result == 0:
            raise ValueError(f"Failed to read binary tag {self.name}")
        return bytes(data)

    def as_string(self) -> str:
        """Returns the tag value as a string."""
        if self.type not in (TAG_TYPE_STRING, TAG_TYPE_STRINGREF):
            raise ValueError(f"Tag {self.name} is not a STRING or STRINGREF type")
        ptr = APPHELP.SdbGetStringTagPtr(self.db.handle, self.tag_id)
        return ptr if ptr is not None else ''


class SdbDatabase:
    def __init__(self, path: str, path_type: PathType):
        self.path = path
        self.path_type = path_type
        self.handle = APPHELP.SdbOpenDatabase(path, path_type)
        self._root = None

    def root(self):
        if self._root is None and self.handle is not None:
            self._root = Tag(self, TAGID_ROOT)
        return self._root

    def close(self):
        if self.handle:
            APPHELP.SdbCloseDatabase(self.handle)
            self.handle = None

    def __bool__(self):
        if self.handle is None:
            return False
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
