"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the apphelp.winapi module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import pytest
from ctypes import c_void_p
from sdbtool.apphelp.winapi import (
    APPHELP,
    ATTRINFO,
    SdbFormatAttribute,
    SdbTagToString,
    SdbReadBinaryTag,
)


def test_SdbTagToString_fallback(monkeypatch):
    monkeypatch.setattr(APPHELP, "SdbTagToString", lambda tag: "InvalidTag")

    # First check that the fallback works for these tags
    fallback_tags = [0x7054, 0x7055, 0x7056, 0x7077, 0x7078, 0x7079]
    for tag in fallback_tags:
        assert SdbTagToString(tag) != "InvalidTag"

    assert APPHELP.SdbTagToString(0x1234) == "InvalidTag"

    # Now check that the fallback does not kick in when the tag is valid
    monkeypatch.setattr(APPHELP, "SdbTagToString", lambda tag: "ValidTag")
    for tag in fallback_tags:
        assert SdbTagToString(tag) == "ValidTag"


def test_SdbReadBinaryTag_fails(monkeypatch):
    monkeypatch.setattr(APPHELP, "SdbGetTagDataSize", lambda pdb, tagid: 1)
    monkeypatch.setattr(APPHELP, "SdbReadBinaryTag", lambda pdb, tagid, buffer, size: 0)

    # Check that the function raises an error when trying to read a binary tag that should succeed, but doesn't
    with pytest.raises(ValueError, match="Failed to read binary tag"):
        SdbReadBinaryTag(c_void_p(), 0x1234)


def test_SdbFormatAttribute_fails(monkeypatch):
    monkeypatch.setattr(APPHELP, "SdbFormatAttribute", lambda attr, buf, size: 0)

    attr = ATTRINFO()
    attr.tAttrID = 0x7001  # TAG_DATABASE

    # Check that the function raises an error when trying to format an attribute that should succeed, but fails
    with pytest.raises(ValueError, match="Failed to format attribute \\(DATABASE\\)"):
        SdbFormatAttribute(attr)
