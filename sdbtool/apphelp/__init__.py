"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     High level interface to the AppHelp API for reading SDB files.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from ctypes import c_void_p
from enum import IntEnum, IntFlag
from base64 import b64encode
import sdbtool.apphelp.winapi as apphelp


TAG_NULL = 0x0
TAGID_NULL = 0x0
TAGID_ROOT = 0x0


class PathType(IntEnum):
    DOS_PATH = 0
    NT_PATH = 1


class IndexFlags(IntFlag):
    SHIMDB_INDEX_UNIQUE_KEY = (
        0x1  # https://learn.microsoft.com/en-us/windows/win32/devnotes/sdbgetindex
    )
    SHIMDB_INDEX_TRAILING_CHARACTERS = 0x2


class TagType(IntEnum):
    """Enumeration of tag types."""

    NULL = 0x1000  # TAG_TYPE_NULL
    BYTE = 0x2000  # TAG_TYPE_BYTE
    WORD = 0x3000  # TAG_TYPE_WORD
    DWORD = 0x4000  # TAG_TYPE_DWORD
    QWORD = 0x5000  # TAG_TYPE_QWORD
    STRINGREF = 0x6000  # TAG_TYPE_STRINGREF
    LIST = 0x7000  # TAG_TYPE_LIST
    STRING = 0x8000  # TAG_TYPE_STRING
    BINARY = 0x9000  # TAG_TYPE_BINARY
    MASK = 0xF000  # TAG_TYPE_MASK


class PlatformType(IntFlag):
    X86 = 0x1
    AMD64 = 0x2
    X86_ON_AMD64 = 0x4
    ARM = 0x8
    ARM64 = 0x10


TAG_OS_PLATFORM = 0x23 | TagType.DWORD  # AKA GUEST_TARGET_PLATFORM
TAG_RUNTIME_PLATFORM = 0x21 | TagType.DWORD


def get_tag_type(tag: int) -> TagType:
    """Extracts the type from a tag."""
    return TagType(tag & TagType.MASK)


def tag_id_to_string(tag: int) -> str:
    """Converts a tag to its string representation."""
    return apphelp.SdbTagToString(tag)


def _value_to_flags(value: int, flags: type[IntFlag]) -> str:
    """Converts a value to a string representation of its flags."""
    values = []
    for flag in flags:
        if value & flag:
            values.append(flag.name)
            value &= ~flag
    if value != 0:
        values.append(f"{value:#x}")
    return " | ".join(values) if values else "0x0"


def tag_value_to_string(tag: "Tag") -> tuple[str | None, str | None]:
    if tag.type == TagType.BYTE:
        return (
            None,
            "UNHANDLED BYTE TAG, please report this at https://github.com/learn-more/sdbtool",
        )
    elif tag.type == TagType.WORD:
        value = tag.read_word()
        if tag.name in ("INDEX_TAG", "INDEX_KEY"):
            return f"{value}", f"{tag_id_to_string(value)}"
        return f"{value}", None
    elif tag.type == TagType.DWORD:
        value = tag.read_dword()
        comment = None
        if tag.name in ("INDEX_FLAGS",):
            comment = _value_to_flags(value, IndexFlags)
        elif tag.tag in (TAG_OS_PLATFORM, TAG_RUNTIME_PLATFORM):
            comment = _value_to_flags(value, PlatformType)
        return f"{value}", comment
    elif tag.type == TagType.QWORD:
        return f"{tag.read_qword()}", None
    elif tag.type in (TagType.STRINGREF, TagType.STRING):
        val = tag.read_string()
        return val, None
    elif tag.type == TagType.BINARY:
        data = tag.read_bytes()
        if data:
            base64_data = b64encode(data).decode("utf-8")
            if tag.name.endswith("_ID") and len(data) == 16:
                guid_str = guid_to_string(data)
                return base64_data, f"{{{guid_str}}}"
            return base64_data, None
        return "", None
    raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")


def guid_to_string(guid: bytes) -> str:
    """Converts a GUID (16-byte binary) to its string representation."""
    if len(guid) != 16:
        raise ValueError("GUID must be 16 bytes long")
    return (
        f"{guid[3]:02x}{guid[2]:02x}{guid[1]:02x}{guid[0]:02x}-"
        f"{guid[5]:02x}{guid[4]:02x}-"
        f"{guid[7]:02x}{guid[6]:02x}-"
        f"{guid[8]:02x}{guid[9]:02x}-"
        f"{guid[10]:02x}{guid[11]:02x}{guid[12]:02x}{guid[13]:02x}{guid[14]:02x}{guid[15]:02x}"
    )


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
            self.type = get_tag_type(self.tag)

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

    def read_word(self, default: int = 0) -> int:
        """Returns the tag value as a word (16-bit integer)."""
        if self.type != TagType.WORD:
            raise ValueError(f"Tag {self.name} is not a WORD type")
        return apphelp.SdbReadWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def read_dword(self, default: int = 0) -> int:
        """Returns the tag value as a dword (32-bit integer)."""
        if self.type != TagType.DWORD:
            raise ValueError(f"Tag {self.name} is not a DWORD type")
        return apphelp.SdbReadDWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def read_qword(self, default: int = 0) -> int:
        """Returns the tag value as a qword (64-bit integer)."""
        if self.type != TagType.QWORD:
            raise ValueError(f"Tag {self.name} is not a QWORD type")
        return apphelp.SdbReadQWORDTag(self._ensure_db_handle(), self.tag_id, default)

    def read_bytes(self) -> bytes:
        """Returns the tag value as bytes."""
        if self.type != TagType.BINARY:
            raise ValueError(f"Tag {self.name} is not a BINARY type")
        return apphelp.SdbReadBinaryTag(self._ensure_db_handle(), self.tag_id)

    def read_string(self) -> str:
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
