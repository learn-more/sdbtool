"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the pure-Python SDB reader edge cases.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

import struct
import pytest
from sdbtool.apphelp import sdb_reader as r
from sdbtool.apphelp.sdb_reader import SdbFile


def W(v: int) -> bytes:
    return struct.pack("<H", v)


def D(v: int) -> bytes:
    return struct.pack("<I", v)


def mk(data: bytes, stringtable: int = 0) -> SdbFile:
    pdb = SdbFile(data, 2, 0)
    pdb.stringtable = stringtable
    return pdb


def test_read_data_bounds():
    pdb = mk(b"abcd")
    assert r.SdbpReadData(pdb, 0, 0) is None  # nothing to read / overflow guard
    assert r.SdbpReadData(pdb, 0, 10) is None  # out of bounds
    assert r.SdbpReadData(pdb, 0, 2) == b"ab"


def test_get_tag_out_of_bounds():
    assert r.SdbGetTagFromTagID(mk(b""), 0) == r.TAG_NULL


def test_get_tag_data_size():
    assert r.SdbGetTagDataSize(mk(W(0x0000)), 0) == 0  # NULL nibble
    assert r.SdbGetTagDataSize(mk(W(0x4000)), 0) == 4  # fixed DWORD
    assert r.SdbGetTagDataSize(mk(W(0x7000) + D(5)), 0) == 5  # dynamic list
    assert r.SdbGetTagDataSize(mk(W(0x7000)), 0) == 0  # truncated size


def test_tag_size_padding():
    assert r._sdbp_get_tag_size(mk(W(0x0000)), 0) == 0  # NULL nibble
    assert r._sdbp_get_tag_size(mk(W(0x2000) + b"\x01"), 0) == 4  # BYTE -> pad to 2
    assert r._sdbp_get_tag_size(mk(W(0x7000) + D(4) + b"....", 0), 0) == 10


# Tags never live at offset 0 in a real database (that is the 12-byte header /
# TAGID_ROOT), so crafted buffers prepend a header so tag ids are non-zero.
HDR = b"\x00" * 12


def test_first_child():
    assert r.SdbGetFirstChild(mk(b"x" * 12), r.TAGID_ROOT) == r.TAGID_NULL
    assert r.SdbGetFirstChild(mk(b"x" * 16), r.TAGID_ROOT) == r._TAGID_ROOT
    assert (
        r.SdbGetFirstChild(mk(HDR + W(0x4000) + D(0)), 12) == r.TAGID_NULL
    )  # not list
    assert r.SdbGetFirstChild(mk(HDR + W(0x7000) + D(0)), 12) == r.TAGID_NULL  # empty
    pdb = mk(HDR + W(0x7000) + D(4) + W(0x4000) + D(0))
    assert r.SdbGetFirstChild(pdb, 12) == 18  # 12 + sizeof(TAG) + sizeof(DWORD)


def test_next_child():
    # prev_child is a NULL-nibble tag -> size 0 -> no next
    assert (
        r.SdbGetNextChild(mk(HDR + W(0x0000) + b"\x00" * 8), r.TAGID_ROOT, 12)
        == r.TAGID_NULL
    )
    # next_child runs past the end of the database
    pdb = mk(HDR + W(0x4000) + D(0))  # one DWORD tag at 12
    assert r.SdbGetNextChild(pdb, r.TAGID_ROOT, 12) == r.TAGID_NULL
    # ROOT parent: returns the next tag
    pdb = mk(HDR + W(0x4000) + D(0) + W(0x4000) + D(0))
    assert r.SdbGetNextChild(pdb, r.TAGID_ROOT, 12) == 18
    # parent has zero size (points at a NULL-nibble tag) -> no next
    pdb = mk(HDR + W(0x4000) + D(0) + W(0x4000) + D(0) + W(0x0000))
    assert r.SdbGetNextChild(pdb, 24, 12) == r.TAGID_NULL
    # next_child is outside the parent's range (list size only covers first child)
    pdb = mk(HDR + W(0x7000) + D(6) + W(0x4000) + D(0) + W(0x4000) + D(0))
    assert r.SdbGetNextChild(pdb, 12, 18) == r.TAGID_NULL


def test_find_first_tag():
    pdb = mk(W(0x7000) + D(12) + W(0x4001) + D(0) + W(0x4002) + D(0))
    assert r.SdbFindFirstTag(pdb, 0, 0x4002) == 12
    assert r.SdbFindFirstTag(pdb, 0, 0x9999) == r.TAGID_NULL


def test_read_scalar_wrong_type_returns_default():
    pdb = mk(W(0x4000) + D(7))  # a DWORD tag
    assert r.SdbReadDWORDTag(pdb, 0) == 7
    assert r.SdbReadBYTETag(pdb, 0, default=9) == 9
    assert r.SdbReadWORDTag(pdb, 0, default=9) == 9
    assert r.SdbReadQWORDTag(pdb, 0, default=9) == 9
    # correct types
    assert r.SdbReadBYTETag(mk(W(0x2000) + b"\xab"), 0) == 0xAB
    assert r.SdbReadWORDTag(mk(W(0x3000) + W(0xABCD)), 0) == 0xABCD
    assert r.SdbReadQWORDTag(mk(W(0x5000) + struct.pack("<Q", 5)), 0) == 5
    # correct type but truncated value falls back to default
    assert r.SdbReadBYTETag(mk(W(0x2000)), 0, default=3) == 3
    assert r.SdbReadWORDTag(mk(W(0x3000)), 0, default=3) == 3
    assert r.SdbReadDWORDTag(mk(W(0x4000)), 0, default=3) == 3
    assert r.SdbReadQWORDTag(mk(W(0x5000)), 0, default=3) == 3
    # wrong type for DWORD falls back to default
    assert r.SdbReadDWORDTag(mk(W(0x2000) + b"\x00"), 0, default=3) == 3


def test_read_binary_tag():
    assert r.SdbReadBinaryTag(mk(W(0x9000) + D(0)), 0) == b""
    assert r.SdbReadBinaryTag(mk(W(0x9000) + D(2) + b"hi"), 0) == b"hi"
    with pytest.raises(ValueError, match="is not a binary tag"):
        r.SdbReadBinaryTag(mk(W(0x4000) + D(0)), 0)
    with pytest.raises(ValueError, match="Failed to read binary tag"):
        r.SdbReadBinaryTag(mk(W(0x9000)), 0)  # missing size
    with pytest.raises(ValueError, match="Failed to read binary tag"):
        r.SdbReadBinaryTag(mk(W(0x9000) + D(10) + b"hi"), 0)  # truncated data


def _string_tag(text: str) -> bytes:
    raw = text.encode("utf-16-le") + b"\x00\x00"
    return W(0x8000) + D(len(raw)) + raw


def test_string_tag_ptr():
    assert r.SdbGetStringTagPtr(mk(b""), 0) is None  # TAG_NULL
    # STRING type, inline
    assert r.SdbGetStringTagPtr(mk(_string_tag("hello")), 0) == "hello"
    # non-string type
    assert r.SdbGetStringTagPtr(mk(W(0x4000) + D(0)), 0) is None
    # STRINGREF without a string table
    assert r.SdbGetStringTagPtr(mk(W(0x6000) + D(0), stringtable=0), 0) is None
    # STRINGREF with a table but truncated offset
    assert r.SdbGetStringTagPtr(mk(W(0x6000), stringtable=4), 0) is None
    # STRING with missing size dword
    assert r.SdbGetStringTagPtr(mk(W(0x8000)), 0) is None
    # STRING whose declared data is missing
    assert r.SdbGetStringTagPtr(mk(W(0x8000) + D(100)), 0) is None
    # STRING with malformed (odd-length) UTF-16 data
    assert r.SdbGetStringTagPtr(mk(W(0x8000) + D(1) + b"\x00"), 0) is None


def test_stringref_resolution():
    # Build: [STRING-table list][stringref]. Lay out so the stringref resolves.
    # stringtable list at offset 0: TAG(0x7801) + size; item is a STRING entry.
    payload = "AB".encode("utf-16-le") + b"\x00\x00"
    item = W(0x8801) + D(len(payload)) + payload  # string-table entry
    table = W(0x7801) + D(len(item)) + item  # table header (6 bytes) + item
    item_off = 6  # offset of the item relative to the table start
    # The stringref stores the offset of the item relative to the table start.
    sref = W(0x6001) + D(item_off)
    data = HDR + table + sref
    pdb = mk(data, stringtable=12)  # table starts right after the 12-byte header
    sref_tagid = 12 + len(table)
    assert r.SdbGetStringTagPtr(pdb, sref_tagid) == "AB"


def test_resolve_metadata_non16_id_and_unresolved_name():
    # DATABASE { DATABASE_ID (4 bytes), NAME (stringref, no string table) }
    id_child = W(0x9007) + D(4) + b"ABCD"
    name_child = W(0x6001) + D(0)
    children = id_child + name_child
    database = W(0x7001) + D(len(children)) + children
    pdb = mk(HDR + database)
    r._resolve_metadata(pdb)
    assert pdb.database_id is None  # 4 bytes != 16 -> not a GUID
    assert pdb.database_name is None  # stringref with no string table


def test_resolve_metadata_truncated_id():
    # DATABASE_ID claims 16 bytes but the data is truncated -> read raises -> ignored.
    id_child = W(0x9007) + D(16) + b"AB"
    database = W(0x7001) + D(len(id_child)) + id_child
    pdb = mk(HDR + database)
    r._resolve_metadata(pdb)
    assert pdb.database_id is None


def test_open_database(tmp_path):
    assert r.SdbOpenDatabase(str(tmp_path / "missing.sdb")) is None  # OSError
    bad = tmp_path / "bad.sdb"
    bad.write_bytes(b"short")
    assert r.SdbOpenDatabase(str(bad)) is None  # too short / bad magic
    badmagic = tmp_path / "bm.sdb"
    badmagic.write_bytes(D(2) + D(0) + b"XXXX")
    assert r.SdbOpenDatabase(str(badmagic)) is None  # wrong magic
    badver = tmp_path / "bv.sdb"
    badver.write_bytes(D(9) + D(0) + b"sdbf")
    assert r.SdbOpenDatabase(str(badver)) is None  # unsupported major
    ok = tmp_path / "ok.sdb"
    ok.write_bytes(D(2) + D(1) + b"sdbf")
    pdb = r.SdbOpenDatabase(str(ok))
    assert pdb is not None and pdb.major == 2 and pdb.minor == 1
