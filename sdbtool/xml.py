"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Xml writer + visitor for SDB files.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import TagVisitor, Tag, TagType, tag_to_string
from xml.sax.saxutils import escape, quoteattr
from base64 import b64encode

INDENT_DEPTH = 2  # Number of spaces for each indentation level in XML output


def tagtype_to_xmltype(tag_type: TagType) -> str | None:
    switch = {
        TagType.BYTE: "xs:byte",
        TagType.WORD: "xs:unsignedShort",
        TagType.DWORD: "xs:unsignedInt",
        TagType.QWORD: "xs:unsignedLong",
        TagType.STRINGREF: "xs:string",
        TagType.STRING: "xs:string",
        TagType.BINARY: "xs:base64Binary",
    }
    return switch.get(tag_type, None)


class XmlWriter:
    def __init__(self, stream):
        self._stream = stream

    def write_xml_declaration(self):
        """Write the XML declaration at the start of the document."""
        self._stream.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')

    def indent(self, level):
        """Return the indentation string for the given level."""
        self._stream.write("\n")
        self._stream.write(" " * (level * INDENT_DEPTH))
        return self

    def open(self, name, attrib=None):
        """Open an XML tag with the given name and attributes."""
        self._stream.write(f"<{name}")
        if attrib:
            for key, value in attrib.items():
                self._stream.write(f' {key}={quoteattr(value)}')
        self._stream.write(">")
        return self

    def close(self, name):
        """Close an XML tag with the given name."""
        self._stream.write(f"</{name}>")

    def empty_tag(self, name):
        """Write an empty XML tag with the given name and attributes."""
        self._stream.write(f"<{name} />")

    def write(self, text):
        """Write text content to the XML stream."""
        self._stream.write(text)


class XmlTagVisitor(TagVisitor):
    def __init__(self, stream, input_filename: str):
        """Initialize the XML tag visitor with a filename."""
        self.writer = XmlWriter(stream)
        self.writer.write_xml_declaration()
        self._depth = 0
        self._input_filename = input_filename
        self._indent_on_close = False

    def visit_list_begin(self, tag: Tag):
        """Visit the beginning of a list tag."""

        attrs = None
        if self._depth == 0:
            attrs = {
                "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
                "file": self._input_filename,
            }

        self.writer.indent(self._depth).open(tag.name, attrs)
        self._depth += 1
        self._indent_on_close = False

    def visit_list_end(self, tag: Tag):
        """Visit the end of a list tag."""
        self._depth -= 1
        if self._indent_on_close:
            self.writer.indent(self._depth)
        self.writer.close(tag.name)
        self._indent_on_close = True

    def visit(self, tag: Tag):
        """Visit a tag."""
        self._indent_on_close = True
        if tag.type == TagType.NULL:
            self.writer.indent(self._depth).empty_tag(tag.name)
            return

        attrs = {}
        if tag.type != TagType.LIST:
            typename = tagtype_to_xmltype(tag.type)
            if typename is not None:
                attrs["type"] = typename
            else:
                raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")

        self.writer.indent(self._depth).open(tag.name, attrs)
        self._write_tag_value(tag)
        self.writer.close(tag.name)

    def _write_tag_value(self, tag: Tag):
        """Write the value of a tag based on its type."""
        if tag.type == TagType.BYTE:
            self.writer.write(
                "<!-- UNHANDLED BYTE TAG, please report this at https://github.com/learn-more/sdbtool -->"
            )
        elif tag.type == TagType.WORD:
            value = tag.as_word()
            self.writer.write(f"{value}")
            if tag.name in ("INDEX_TAG", "INDEX_KEY"):
                self.writer.write(f"<!-- {tag_to_string(value)} -->")
        elif tag.type == TagType.DWORD:
            self.writer.write(f"{tag.as_dword()}")
        elif tag.type == TagType.QWORD:
            self.writer.write(f"{tag.as_qword()}")
        elif tag.type in (TagType.STRINGREF, TagType.STRING):
            val = tag.as_string()
            if val:
                self.writer.write(f"{escape(val)}")
        elif tag.type == TagType.BINARY:
            data = tag.as_bytes()
            if data:
                base64_data = b64encode(data).decode("utf-8")
                self.writer.write(base64_data)
        else:
            raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")
