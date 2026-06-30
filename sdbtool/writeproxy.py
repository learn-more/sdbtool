"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Stream-writer proxy that resolves the target .write once.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>
"""

from __future__ import annotations


class WriteProxy:
    """Expose a concrete ``write`` attribute bound to ``stream.write``.

    The JSON / XML serializers emit the output as a large number of small
    fragments. When the destination is a Click ``LazyFile``, every ``.write``
    lookup runs ``LazyFile.__getattr__`` (which also lazily opens the file),
    so streaming straight to it pays that indirection per fragment and
    dominates the runtime.

    Resolving ``stream.write`` once (which opens a ``LazyFile`` a single time)
    and handing the serializer this proxy keeps the output streaming - no need
    to materialize the whole document in memory - while every subsequent write
    hits a plain attribute with no ``__getattr__`` cost.
    """

    __slots__ = ("write",)

    def __init__(self, stream):
        self.write = stream.write
