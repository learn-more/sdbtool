"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Wrapper around the low level apphelp file attributes API
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import os
from sdbtool.apphelp.winapi import (
    GetFileAttributes,
    SdbFormatAttribute,
    SdbFreeFileAttributes,
    ATTRIBUTE_AVAILABLE,
)


def get_attributes(file_name: str | os.PathLike) -> list[str]:
    attr_info, attr_count = GetFileAttributes(os.fspath(file_name))
    res = [
        SdbFormatAttribute(attr_info[i])
        for i in range(attr_count.value)
        if attr_info[i].dwFlags & ATTRIBUTE_AVAILABLE != 0
    ]
    SdbFreeFileAttributes(attr_info)
    return res
