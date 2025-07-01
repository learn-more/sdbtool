"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the guid_to_string function in the apphelp module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import guid_to_string
from base64 import b64decode
import pytest


def test_guid_to_string():
    # Test with a valid GUID
    guid_str = "Wy8It8yzrESgMGnvPjUiXQ=="
    guid = b64decode(guid_str)
    expected = "b7082f5b-b3cc-44ac-a030-69ef3e35225d"
    assert guid_to_string(guid) == expected

    # Test with an invalid GUID length
    with pytest.raises(ValueError, match="GUID must be 16 bytes long"):
        guid_to_string(bytes.fromhex("12345678"))
