"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     winapi interface to the AppHelp API for reading SDB files.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from ctypes import (
    byref,
    create_unicode_buffer,
    windll,
    c_void_p,
    c_uint16,
    c_uint32,
    c_wchar_p,
    POINTER,
    pointer,
    c_ubyte,
    c_uint64,
    Structure,
    Union,
)

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


# typedef struct tagATTRINFO {
#   TAG   tAttrID;
#   DWORD dwFlags;
#   union {
#     ULONGLONG ullAttr;
#     DWORD     dwAttr;
#     TCHAR     *lpAttr;
#   };
# } ATTRINFO, *PATTRINFO;


class _U(Union):
    _fields_ = [("ullAttr", c_uint64), ("dwAttr", c_uint32), ("lpAttr", c_wchar_p)]


class ATTRINFO(Structure):
    _anonymous_ = ("_u",)
    _fields_ = [
        ("tAttrID", c_uint16),  # TAG
        ("dwFlags", c_uint32),
        ("_u", _U),  # Union for ullAttr, dwAttr, lpAttr
    ]


ATTRIBUTE_AVAILABLE = 0x00000001  # Attribute is available


# BOOL WINAPI SdbFormatAttribute(
#   _In_  PATTRINFO pAttrInfo,
#   _Out_ LPTSTR    pchBuffer,
#   _In_  DWORD     dwBufferSize
# );
APPHELP.SdbFormatAttribute.argtypes = [POINTER(ATTRINFO), c_wchar_p, c_uint32]
APPHELP.SdbFormatAttribute.restype = c_uint32

# BOOL WINAPI SdbGetFileAttributes(
#   _In_  LPCTSTR   lpwszFileName,
#   _Out_ PATTRINFO *ppAttrInfo,
#   _Out_ LPDWORD   lpdwAttrCount
# );
APPHELP.SdbGetFileAttributes.argtypes = [
    c_wchar_p,
    POINTER(POINTER(ATTRINFO)),
    POINTER(c_uint32),
]
APPHELP.SdbGetFileAttributes.restype = c_uint32

# BOOL WINAPI SdbFreeFileAttributes(
#   _In_ PATTRINFO pFileAttributes
# );
APPHELP.SdbFreeFileAttributes.argtypes = [c_void_p]
APPHELP.SdbFreeFileAttributes.restype = c_uint32


# BOOL WINAPI SdbGetMatchingExe(
#   _In_opt_ HSDB            hSDB,
#   _In_     LPCTSTR         szPath,
#   _In_opt_ LPCTSTR         szModuleName,
#   _In_opt_ LPCTSTR         pszEnvironment,
#   _In_     DWORD           dwFlags,
#   _Out_    PSDBQUERYRESULT pQueryResult
# );
APPHELP.SdbGetMatchingExe.argtypes = [
    c_void_p,
    c_wchar_p,
    c_wchar_p,
    c_wchar_p,
    c_uint32,
    POINTER(c_void_p),
]
APPHELP.SdbGetMatchingExe.restype = c_uint32

# void WINAPI SdbReleaseMatchingExe(
#   _In_ HSDB   hSDB,
#   _In_ TAGREF trExe
# );
APPHELP.SdbReleaseMatchingExe.argtypes = [c_void_p, c_uint32]
APPHELP.SdbReleaseMatchingExe.restype = None


def SdbOpenDatabase(path: str, path_type: int) -> c_void_p:
    """Open a database at the specified path."""
    return APPHELP.SdbOpenDatabase(path, path_type)


def SdbCloseDatabase(db: c_void_p):
    """Close the specified database."""
    APPHELP.SdbCloseDatabase(db)


def SdbGetFirstChild(db: c_void_p, parent: int) -> int:
    """Get the first child tag of the specified parent."""
    return APPHELP.SdbGetFirstChild(db, parent)


def SdbGetNextChild(db: c_void_p, parent: int, prev_child: int) -> int:
    """Get the next child tag of the specified parent."""
    return APPHELP.SdbGetNextChild(db, parent, prev_child)


def SdbGetTagFromTagID(db: c_void_p, tag_id: int) -> int:
    """Get the tag from the specified tag ID."""
    return APPHELP.SdbGetTagFromTagID(db, tag_id)


def SdbTagToString(tag: int) -> str:
    """Convert a tag to its string representation."""
    return APPHELP.SdbTagToString(tag)


def SdbReadWORDTag(db: c_void_p, tag_id: int, default: int = 0) -> int:
    """Read a WORD tag from the database."""
    return APPHELP.SdbReadWORDTag(db, tag_id, default)


def SdbReadDWORDTag(db: c_void_p, tag_id: int, default: int = 0) -> int:
    """Read a DWORD tag from the database."""
    return APPHELP.SdbReadDWORDTag(db, tag_id, default)


def SdbReadQWORDTag(db: c_void_p, tag_id: int, default: int = 0) -> int:
    """Read a QWORD tag from the database."""
    return APPHELP.SdbReadQWORDTag(db, tag_id, default)


def SdbReadBinaryTag(db: c_void_p, tag_id: int) -> bytes:
    """Read a binary tag from the database."""
    size = APPHELP.SdbGetTagDataSize(db, tag_id)
    if size == 0:
        return b""
    data = (c_ubyte * size)()
    result = APPHELP.SdbReadBinaryTag(db, tag_id, data, size)
    if result == 0:
        raise ValueError(f"Failed to read binary tag 0x{tag_id:x}")
    return bytes(data)


def SdbGetStringTagPtr(db: c_void_p, tag_id: int) -> str:
    """Get the string pointer of the specified tag."""
    return APPHELP.SdbGetStringTagPtr(db, tag_id)


def GetFileAttributes(file_name: str):
    """Get file attributes for the specified file."""
    attr_info = POINTER(ATTRINFO)()
    attr_count = c_uint32()
    result = APPHELP.SdbGetFileAttributes(
        file_name, byref(attr_info), byref(attr_count)
    )
    if result == 0:
        raise ValueError(f"Failed to get file attributes for '{file_name}'")
    return attr_info, attr_count


def SdbFormatAttribute(attr_info: ATTRINFO) -> str:
    """Format the attribute information into a string."""
    buffer_size = 1024 * 2
    buffer = create_unicode_buffer(buffer_size)
    result = APPHELP.SdbFormatAttribute(pointer(attr_info), buffer, buffer_size)
    if result == 0:
        name = SdbTagToString(attr_info.tAttrID)
        raise ValueError(f"Failed to format attribute ({name})")
    return buffer.value if buffer.value else ""


def SdbFreeFileAttributes(attr_info):
    """Free the file attributes structure."""
    APPHELP.SdbFreeFileAttributes(attr_info)
