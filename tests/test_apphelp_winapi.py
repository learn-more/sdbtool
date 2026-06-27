"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the pure-Python apphelp reader / file-attribute layer.
COPYRIGHT:   Copyright 2025,2026 Mark Jansen <mark.jansen@reactos.org>
"""

import pytest
from sdbtool.apphelp import sdb_reader
from sdbtool.apphelp.fileattr import AttrInfo, format_attribute, ATTRIBUTE_FAILED


def test_SdbReadBinaryTag_not_binary():
    # A zero-length buffer has no valid tags, so reading a binary tag must fail.
    pdb = sdb_reader.SdbFile(b"", 2, 0)
    with pytest.raises(ValueError, match="is not a binary tag"):
        sdb_reader.SdbReadBinaryTag(pdb, 0x1234)


def test_SdbReadBinaryTag_truncated(monkeypatch):
    pdb = sdb_reader.SdbFile(b"", 2, 0)
    # Pretend there is a binary tag, but the data cannot be read.
    monkeypatch.setattr(sdb_reader, "_check_type", lambda *a: True)
    with pytest.raises(ValueError, match="Failed to read binary tag"):
        sdb_reader.SdbReadBinaryTag(pdb, 0x1234)


def test_format_attribute_fails():
    attr = AttrInfo(0x7001, ATTRIBUTE_FAILED, None)  # TAG_DATABASE
    with pytest.raises(ValueError, match="Failed to format attribute \\(DATABASE\\)"):
        format_attribute(attr)
