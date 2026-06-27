"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Wrapper around the file attributes API
COPYRIGHT:   Copyright 2025,2026 Mark Jansen <mark.jansen@reactos.org>
"""

import os
from sdbtool.apphelp.fileattr import (
    get_file_attributes,
    format_attribute,
    ATTRIBUTE_AVAILABLE,
)


def get_attributes(file_name: str | os.PathLike) -> list[str]:
    try:
        attrs = get_file_attributes(file_name)
    except OSError as e:
        raise ValueError(f"Failed to get file attributes for '{file_name}'") from e
    return [
        format_attribute(attr)
        for attr in attrs
        if attr.flags & ATTRIBUTE_AVAILABLE != 0
    ]
