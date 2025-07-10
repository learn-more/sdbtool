"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the guid_to_string function in the apphelp module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.attributes import get_attributes
import pytest


def test_get_attributes():
    # Test with a valid file
    file_name = "tests/data/test_x32.exe"
    expected = [
        'SIZE="2048"',
        'FILESIZE="2048"',
        'SIZE_OF_IMAGE="0x3000"',
        'CHECKSUM="0xADD9AAFF"',
        'BIN_FILE_VERSION="1.0.0.0"',
        'BIN_PRODUCT_VERSION="1.0.0.1"',
        'PRODUCT_VERSION="1.0.0.1"',
        'FILE_DESCRIPTION="FileDescription"',
        'COMPANY_NAME="CompanyName"',
        'PRODUCT_NAME="Productname"',
        'FILE_VERSION="1.0.0.0"',
        'ORIGINAL_FILENAME="OriginalFilename"',
        'INTERNAL_NAME="InternalName"',
        'LEGAL_COPYRIGHT="LegalCopyright"',
        'VERDATEHI="0x0"',
        'VERDATELO="0x0"',
        'VERFILEOS="0x4"',
        'VERFILETYPE="0x1"',
        'MODULE_TYPE="WIN32"',
        'PE_CHECKSUM="0x1655"',
        'LINKER_VERSION="0x0"',
        'FROM_BIN_FILE_VERSION="1.0.0.0"',
        'FROM_BIN_PRODUCT_VERSION="1.0.0.1"',
        'UPTO_BIN_FILE_VERSION="1.0.0.0"',
        'UPTO_BIN_PRODUCT_VERSION="1.0.0.1"',
        'LINK_DATE="01/01/1970 00:00:00"',
        'FROM_LINK_DATE="01/01/1970 00:00:00"',
        'UPTO_LINK_DATE="01/01/1970 00:00:00"',
        'VER_LANGUAGE="Language Neutral [0xffff]"',
        'EXE_WRAPPER="0x0"',
        'CRC_CHECKSUM="0x9A754E1E"',
        # These do not exist on older versions of apphelp.dll
        # 'FROM_PRODUCT_VERSION="1.0.0.1"',
        # 'UPTO_PRODUCT_VERSION="1.0.0.1"',
        # 'FROM_FILE_VERSION="1.0.0.0"',
        # 'UPTO_FILE_VERSION="1.0.0.0"',
    ]
    # Check that the attributes contain at least the expected attributes
    # This is necessary because the attributes may vary based on the apphelp.dll version
    # and the test files used.
    assert all(attr in get_attributes(file_name) for attr in expected)

    file_name = "tests/data/test_x64.exe"
    expected = [
        'SIZE="2560"',
        'FILESIZE="2560"',
        'SIZE_OF_IMAGE="0x4000"',
        'CHECKSUM="0x7E4FF93C"',
        'BIN_FILE_VERSION="1.0.0.0"',
        'BIN_PRODUCT_VERSION="1.0.0.1"',
        'PRODUCT_VERSION="1.0.0.1"',
        'FILE_DESCRIPTION="FileDescription"',
        'COMPANY_NAME="CompanyName"',
        'PRODUCT_NAME="Productname"',
        'FILE_VERSION="1.0.0.0"',
        'ORIGINAL_FILENAME="OriginalFilename"',
        'INTERNAL_NAME="InternalName"',
        'LEGAL_COPYRIGHT="LegalCopyright"',
        'VERDATEHI="0x0"',
        'VERDATELO="0x0"',
        'VERFILEOS="0x4"',
        'VERFILETYPE="0x1"',
        'MODULE_TYPE="WIN32"',
        'PE_CHECKSUM="0xEC7A"',
        'LINKER_VERSION="0x0"',
        'FROM_BIN_FILE_VERSION="1.0.0.0"',
        'FROM_BIN_PRODUCT_VERSION="1.0.0.1"',
        'UPTO_BIN_FILE_VERSION="1.0.0.0"',
        'UPTO_BIN_PRODUCT_VERSION="1.0.0.1"',
        'LINK_DATE="01/01/1970 00:00:00"',
        'FROM_LINK_DATE="01/01/1970 00:00:00"',
        'UPTO_LINK_DATE="01/01/1970 00:00:00"',
        'VER_LANGUAGE="Language Neutral [0xffff]"',
        'EXE_WRAPPER="0x0"',
        'CRC_CHECKSUM="0x5520E521"',
        # These do not exist on older versions of apphelp.dll
        # 'FROM_PRODUCT_VERSION="1.0.0.1"',
        # 'UPTO_PRODUCT_VERSION="1.0.0.1"',
        # 'FROM_FILE_VERSION="1.0.0.0"',
        # 'UPTO_FILE_VERSION="1.0.0.0"',
    ]
    # Check that the attributes contain at least the expected attributes
    # This is necessary because the attributes may vary based on the apphelp.dll version
    # and the test files used.
    assert all(attr in get_attributes(file_name) for attr in expected)

    # Test with an invalid file
    with pytest.raises(ValueError, match="Failed to get file attributes"):
        get_attributes("invalid.exe")
