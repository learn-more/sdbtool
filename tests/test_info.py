from pathlib import Path

import pytest
from sdbtool.info import get_info, DatabaseInformation
from uuid import UUID

TESTDATA_FOLDER = Path(__file__).parent / "data"


def test_info():
    db_info = get_info(TESTDATA_FOLDER / "app_x32.sdb")

    assert isinstance(db_info, DatabaseInformation)
    assert db_info.Description == "app_x32"
    assert db_info.dwMajor == 2
    assert db_info.dwMinor == 3
    assert db_info.dwFlags == 0x10000001
    assert db_info.Id == UUID("83964529-0dd6-4e42-b291-bfd0faa747e9")
    assert db_info.dwRuntimePlatform == 4

    # Test with a file that has no id / description:
    db_info = get_info(TESTDATA_FOLDER / "all_tagtypes.sdb")
    assert isinstance(db_info, DatabaseInformation)
    assert db_info.Description is None
    assert db_info.dwMajor == 3
    assert db_info.dwMinor == 0
    assert db_info.dwFlags == 0x10000000
    assert db_info.Id is None
    assert db_info.dwRuntimePlatform == 4

    with pytest.raises(ValueError, match="Failed to get database information for"):
        get_info(TESTDATA_FOLDER / "nonexistent.sdb")
