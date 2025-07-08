"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Convert SDB files to XML format.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import (
    PathType,
    SdbDatabase,
    TagVisitor,
    TagType,
    Tag,
    tag_to_string,
    guid_to_string,
    SHIMDB_INDEX_UNIQUE_KEY
)
from sdbtool.xml import XmlWriter
from base64 import b64encode
from pathlib import Path


def tagtype_to_xmltype(tag_type: TagType) -> str | None:
    tagtype_map = {
        TagType.BYTE: "xs:byte",
        TagType.WORD: "xs:unsignedShort",
        TagType.DWORD: "xs:unsignedInt",
        TagType.QWORD: "xs:unsignedLong",
        TagType.STRINGREF: "xs:string",
        TagType.STRING: "xs:string",
        TagType.BINARY: "xs:base64Binary",
    }
    return tagtype_map.get(tag_type, None)


class XmlTagVisitor(TagVisitor):
    def __init__(self, stream, input_filename: str):
        """Initialize the XML tag visitor with a filename."""
        self.writer = XmlWriter(stream)
        self._first = True
        self._input_filename = input_filename

    def visit_list_begin(self, tag: Tag):
        """Visit the beginning of a list tag."""
        attrs = None
        if self._first:
            self._first = False
            self.writer.write_xml_declaration()
            attrs = {
                "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
                "file": self._input_filename,
            }
        self.writer.open(tag.name, attrs)

    def visit_list_end(self, tag: Tag):
        """Visit the end of a list tag."""
        self.writer.close(tag.name)

    def visit(self, tag: Tag):
        """Visit a tag."""
        if tag.type == TagType.NULL:
            self.writer.empty_tag(tag.name)
            return

        attrs = {}
        if tag.type != TagType.LIST:
            typename = tagtype_to_xmltype(tag.type)
            if typename is not None:
                attrs["type"] = typename
            else:
                raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")

        self.writer.open(tag.name, attrs)
        self._write_tag_value(tag)
        self.writer.close(tag.name)

    def _write_tag_value(self, tag: Tag):
        """Write the value of a tag based on its type."""
        if tag.type == TagType.BYTE:
            self.writer.write_comment(
                "UNHANDLED BYTE TAG, please report this at https://github.com/learn-more/sdbtool"
            )
        elif tag.type == TagType.WORD:
            value = tag.as_word()
            self.writer.write(f"{value}")
            if tag.name in ("INDEX_TAG", "INDEX_KEY"):
                self.writer.write_comment(f"{tag_to_string(value)}")
        elif tag.type == TagType.DWORD:
            value = tag.as_dword()
            self.writer.write(f"{value}")
            if tag.name in ("INDEX_FLAGS",):
                comment = ""
                if value & SHIMDB_INDEX_UNIQUE_KEY:
                    comment += "1 = SHIMDB_INDEX_UNIQUE_KEY"  # https://learn.microsoft.com/en-us/windows/win32/devnotes/sdbgetindex
                if comment:
                    self.writer.write_comment(comment)
        elif tag.type == TagType.QWORD:
            self.writer.write(f"{tag.as_qword()}")
        elif tag.type in (TagType.STRINGREF, TagType.STRING):
            val = tag.as_string()
            if val:
                self.writer.write(f"{val}")
        elif tag.type == TagType.BINARY:
            data = tag.as_bytes()
            if data:
                base64_data = b64encode(data).decode("utf-8")
                self.writer.write(base64_data)
                if tag.name.endswith("_ID") and len(data) == 16:
                    guid_str = guid_to_string(data)
                    self.writer.write_comment(f"{{{guid_str}}}")
        else:
            raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")


def convert(input_file: str, output_stream):
    with SdbDatabase(input_file, PathType.DOS_PATH) as db:
        if not db:
            raise ValueError(f"Failed to open database at '{input_file}'")

        visitor = XmlTagVisitor(output_stream, Path(input_file).name)
        root = db.root()
        if root is None:
            raise ValueError(f"No root tag found in database '{input_file}'")
        root.accept(visitor)
