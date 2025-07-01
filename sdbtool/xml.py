"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Simple streaming Xml writer
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from xml.sax.saxutils import escape, quoteattr

INDENT_DEPTH = 2  # Number of spaces for each indentation level in XML output


class XmlWriter:
    def __init__(self, stream):
        self._stream = stream
        self._indent_level = 0
        self._indent_on_close = False

    def write_xml_declaration(self):
        """Write the XML declaration at the start of the document."""
        self._stream.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')

    def _indent(self):
        """Return the indentation string for the given level."""
        self._stream.write("\n")
        self._stream.write(" " * (self._indent_level * INDENT_DEPTH))

    def open(self, name, attrib=None):
        """Open an XML tag with the given name and attributes."""
        self._indent()
        self._stream.write(f"<{name}")
        if attrib:
            for key, value in attrib.items():
                self._stream.write(f" {key}={quoteattr(value)}")
        self._stream.write(">")

        self._indent_level += 1
        self._indent_on_close = False

    def close(self, name):
        """Close an XML tag with the given name."""
        self._indent_level -= 1
        if self._indent_on_close:
            self._indent()
        self._stream.write(f"</{name}>")
        self._indent_on_close = True

    def empty_tag(self, name):
        """Write an empty XML tag with the given name and attributes."""
        self._indent()
        self._stream.write(f"<{name} />")
        self._indent_on_close = True

    def write(self, text):
        """Write text content to the XML stream."""
        self._stream.write(escape(text))

    def write_comment(self, comment):
        """Write a comment to the XML stream."""
        self._stream.write(f"<!-- {escape(comment)} -->")
