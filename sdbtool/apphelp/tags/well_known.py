"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     The handful of tags the dumper logic special-cases by identity.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>

These tag numbers are stable across every Windows version, so they are kept as
hand-written constants -- independent of the generated, version-varying name
tables in ``tags.json``. Code that needs to recognise a specific tag (to add a
decoded comment, decide tree expansion, ...) uses these instead of string names.
"""

from enum import IntEnum


class WellKnownTags(IntEnum):
    """Tags referenced directly by the dump/annotation logic."""

    # TAG_TYPE_WORD
    INDEX_TAG = 0x3802
    INDEX_KEY = 0x3803

    # TAG_TYPE_DWORD
    INDEX_FLAGS = 0x4016
    LINK_DATE = 0x401D
    UPTO_LINK_DATE = 0x401E
    RUNTIME_PLATFORM = 0x4021
    GUEST_TARGET_PLATFORM = 0x4023
    FROM_LINK_DATE = 0x4033

    # TAG_TYPE_QWORD
    TIME = 0x5001

    # TAG_TYPE_LIST
    DATABASE = 0x7001
