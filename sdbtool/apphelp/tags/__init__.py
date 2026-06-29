"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Version-aware SDB tag-name resolution.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>

The tag-id -> name tables are extracted offline from every ``apphelp.dll`` version
by ``tools/generate_tags.py`` and vendored as ``tags.json`` (a ``base`` table plus
per-version ``add`` / ``override`` / ``remove`` deltas). sdbtool therefore needs no
dependency on apphelp at runtime.

Tag names change meaning between Windows versions (e.g. ``0x4022`` is ``OS_SKU`` on
XP but unused on Win11; ``0x4023`` was ``OS_PLATFORM`` and is now
``GUEST_TARGET_PLATFORM``), so resolution is parameterised by a target OS.
"""

from __future__ import annotations

import json
from importlib.resources import files

from .well_known import WellKnownTags

__all__ = [
    "WellKnownTags",
    "tag_id_to_string",
    "KNOWN_VERSIONS",
    "DEFAULT_VERSION",
]


def _load() -> tuple[dict[str, dict[int, str]], list[str]]:
    """Reconstruct the full per-version tables from the base + delta document."""
    doc = json.loads(
        files(__package__).joinpath("tags.json").read_text(encoding="utf-8")
    )
    base = {int(k, 16): v for k, v in doc["base"].items()}

    tables: dict[str, dict[int, str]] = {}
    order: list[tuple[int, int, str]] = []
    for entry in doc["versions"]:
        table = dict(base)
        for k, name in entry["add"].items():
            table[int(k, 16)] = name
        for k, name in entry["override"].items():
            table[int(k, 16)] = name
        for k in entry["remove"]:
            table.pop(int(k, 16), None)
        tables[entry["name"]] = table
        order.append((entry["version"], entry["build"], entry["name"]))

    order.sort()
    return tables, [name for _, _, name in order]


_TABLES, KNOWN_VERSIONS = _load()
# KNOWN_VERSIONS is ordered oldest -> newest; default to the newest (most complete).
DEFAULT_VERSION = KNOWN_VERSIONS[-1]


def tag_id_to_string(tag: int, os_version: str | None = None) -> str:
    """Resolve ``tag`` to its name for a given target OS.

    ``os_version`` is one of :data:`KNOWN_VERSIONS`; ``None`` selects the newest
    table. If the tag is unknown for that OS, fall back to a *newer* version that
    knows it (so a database carrying a tag added after the target still decodes) --
    but never to an older one, so a tag that was removed before the target stays
    unknown. Anything unresolved becomes ``InvalidTag_0xXXXX``, which keeps the raw
    number visible in the output (and is a valid XML element name, unlike a
    parenthesised form).
    """
    if os_version is None or os_version not in _TABLES:
        os_version = DEFAULT_VERSION

    name = _TABLES[os_version].get(tag)
    if name is not None:
        return name

    # Look only at versions newer than the target (forward compatibility).
    for version in KNOWN_VERSIONS[KNOWN_VERSIONS.index(os_version) + 1 :]:
        name = _TABLES[version].get(tag)
        if name is not None:
            return name

    return f"InvalidTag_0x{tag:04X}"
