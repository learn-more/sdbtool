"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     High level interface to the AppHelp API for reading SDB files.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from ctypes import c_void_p
from enum import IntEnum
import sdbtool.apphelp.winapi as apphelp


class PathType(IntEnum):
    DOS_PATH = 0
    NT_PATH = 1


TAGID_NULL = 0x0
TAGID_ROOT = 0x0
_TAGID_ROOT = 12


class TagType(IntEnum):
    """Enumeration of tag types."""

    NULL = 0x1000
    BYTE = 0x2000
    WORD = 0x3000
    DWORD = 0x4000
    QWORD = 0x5000
    STRINGREF = 0x6000
    LIST = 0x7000
    STRING = 0x8000
    BINARY = 0x9000
    MASK = 0xF000


TAG_NULL = 0x0


def _get_tag_type(tag: int) -> TagType:
    """Extracts the type from a tag."""
    return TagType(tag & TagType.MASK)


def tag_to_string(tag: int) -> str:
    """Converts a tag to its string representation."""
    return apphelp.SdbTagToString(tag)


class Tag:
    def __init__(self, db: "SdbDatabase", tag_id: int):
        self.db = db
        self.tag_id = tag_id
        if tag_id == TAGID_ROOT:
            self.tag = TAG_NULL
            self.name = "SDB"
            self.type = TagType.LIST
        else:
            self.tag = apphelp.SdbGetTagFromTagID(self._ensure_db_handle(), tag_id)
            self.name = apphelp.SdbTagToString(self.tag)
            self.type = _get_tag_type(self.tag)

    def _ensure_db_handle(self) -> c_void_p:
        """Ensures that the database handle is initialized."""
        if self.db._handle is None:
            raise ValueError("Database handle is not initialized")
        return self.db._handle

    def tags(self):
        self._ensure_db_handle()
        child = apphelp.SdbGetFirstChild(self._ensure_db_handle(), self.tag_id)
        while child != 0:
            yield Tag(self.db, child)
            child = apphelp.SdbGetNextChild(
                self._ensure_db_handle(), self.tag_id, child
            )

    def as_word(self, default: int = 0) -> int:
        """Returns the tag value as a word (16-bit integer)."""
        if self.type != TagType.WORD:
            raise ValueError(f"Tag {self.name} is not a WORD type")
        return apphelp.SdbReadWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def as_dword(self, default: int = 0) -> int:
        """Returns the tag value as a dword (32-bit integer)."""
        if self.type != TagType.DWORD:
            raise ValueError(f"Tag {self.name} is not a DWORD type")
        return apphelp.SdbReadDWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def as_qword(self, default: int = 0) -> int:
        """Returns the tag value as a qword (64-bit integer)."""
        if self.type != TagType.QWORD:
            raise ValueError(f"Tag {self.name} is not a QWORD type")
        return apphelp.SdbReadQWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def as_bytes(self) -> bytes:
        """Returns the tag value as bytes."""
        if self.type != TagType.BINARY:
            raise ValueError(f"Tag {self.name} is not a BINARY type")
        return apphelp.SdbReadBinaryTag(self._ensure_db_handle(), self.tag_id)

    def as_string(self) -> str:
        """Returns the tag value as a string."""
        if self.type not in (TagType.STRING, TagType.STRINGREF):
            raise ValueError(f"Tag {self.name} is not a STRING or STRINGREF type")
        ptr = apphelp.SdbGetStringTagPtr(self._ensure_db_handle(), self.tag_id)
        return ptr if ptr is not None else ""

    def accept(self, visitor: "TagVisitor"):
        """Accepts a visitor for this tag."""
        if self.type == TagType.LIST:
            visitor.visit_list_begin(self)
            for child in self.tags():
                child.accept(visitor)
            visitor.visit_list_end(self)
        else:
            # For non-list tags, we just visit this tag
            visitor.visit(self)


class TagVisitor:
    def visit(self, tag: Tag):
        """Visit a tag. Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement visit method")

    def visit_list_begin(self, tag: Tag):
        """Visit a list tag. Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement visit_list_begin method")

    def visit_list_end(self, tag: Tag):
        """Visit the end of a list tag. Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement visit_list_end method")


class SdbDatabase:
    def __init__(self, path: str, path_type: PathType):
        self.path = path
        self.path_type = path_type
        self._handle = apphelp.SdbOpenDatabase(path, path_type)
        self._root = None

    def root(self) -> Tag | None:
        if self._root is None and self._handle is not None:
            self._root = Tag(self, TAGID_ROOT)
        return self._root

    def close(self):
        if self._handle:
            apphelp.SdbCloseDatabase(self._handle)
            self._handle = None

    def __bool__(self):
        if self._handle is None:
            return False
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
