"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Wrapper around the low level apphelp database information API
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import os
from dataclasses import dataclass
from uuid import UUID
from sdbtool.apphelp.winapi import (
    GetDatabaseInformationByName,
    SdbFreeDatabaseInformation,
    DB_INFO_FLAGS_VALID_GUID,
)


@dataclass
class DatabaseInformation:
    """Database information structure."""

    Description: str | None
    dwMajor: int
    dwMinor: int
    dwFlags: int
    Id: UUID | None
    dwRuntimePlatform: int | None


def get_info(file_name: str | os.PathLike) -> DatabaseInformation:
    db_info = GetDatabaseInformationByName(os.fspath(file_name))
    id_value = None
    if db_info.contents.dwFlags & DB_INFO_FLAGS_VALID_GUID:
        data = bytes(db_info.contents.Id)
        id_value = UUID(bytes_le=data)
    res = DatabaseInformation(
        Description=db_info.contents.Description or None,
        dwMajor=db_info.contents.dwMajor,
        dwMinor=db_info.contents.dwMinor,
        dwFlags=db_info.contents.dwFlags,
        Id=id_value,
        dwRuntimePlatform=db_info.contents.dwRuntimePlatform or None,
    )
    SdbFreeDatabaseInformation(db_info)
    return res
