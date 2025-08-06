"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Convert SDB files to XML format.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import (
    SdbDatabase,
    TagVisitor,
    TagType,
    Tag,
    tag_value_to_string,
)
from sdbtool.xml import XmlWriter
import enum


class XmlAnnotations(enum.Enum):
    Disabled = enum.auto()
    Comment = enum.auto()


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
    def __init__(
        self,
        stream,
        input_filename: str,
        exclude_tags: list[str],
        annotations: XmlAnnotations,
        with_tagid: bool,
        with_tag: bool,
    ):
        """Initialize the XML tag visitor with a filename."""
        self.writer = XmlWriter(stream)
        self._first = True
        self._input_filename = input_filename
        self._exclude_tags = exclude_tags
        self._annotations = annotations
        self._with_tagid = with_tagid
        self._with_tag = with_tag
        self._skip_depth = 0

    def visit_list_begin(self, tag: Tag):
        """Visit the beginning of a list tag."""
        if tag.name in self._exclude_tags:
            self._skip_depth += 1
        if self._skip_depth > 0:
            return
        if self._first:
            self._first = False
            self.writer.write_xml_declaration()
            attrs = {
                "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
                "file": self._input_filename,
            }
        else:
            attrs = {}
            if self._with_tagid:
                attrs["tagid"] = f"{tag.tag_id}"
            if self._with_tag:
                attrs["tag"] = f"0x{tag.tag:x}"
        self.writer.open(tag.name, attrs)

    def visit_list_end(self, tag: Tag):
        """Visit the end of a list tag."""
        if self._skip_depth > 0:
            if tag.name in self._exclude_tags:
                self._skip_depth -= 1
            return
        self.writer.close(tag.name)

    def visit(self, tag: Tag):
        """Visit a tag."""
        if self._skip_depth > 0:
            return
        if tag.name in self._exclude_tags:
            return

        ids = {}
        if self._with_tagid:
            ids["tagid"] = f"{tag.tag_id}"
        if self._with_tag:
            ids["tag"] = f"0x{tag.tag:x}"

        if tag.type == TagType.NULL:
            self.writer.empty_tag(tag.name, ids)
            return

        typename = tagtype_to_xmltype(tag.type)
        if typename is None:
            raise ValueError(
                f"Unknown xml tag type: {tag.type.name} for tag {tag.name}"
            )
        attrs = {"type": typename}
        attrs.update(ids)

        self.writer.open(tag.name, attrs)
        self._write_tag_value(tag)
        self.writer.close(tag.name)

    def _write_tag_value(self, tag: Tag):
        value, comment = tag_value_to_string(tag)
        self.writer.write(value)
        if self._annotations == XmlAnnotations.Comment and comment is not None:
            self.writer.write_comment(comment)


def convert(
    db: SdbDatabase,
    output_stream,
    exclude_tags: list[str],
    annotations: XmlAnnotations,
    with_tagid: bool,
    with_tag: bool,
):
    visitor = XmlTagVisitor(
        output_stream,
        db.name,
        exclude_tags,
        annotations,
        with_tagid=with_tagid,
        with_tag=with_tag,
    )
    root = db.root()
    assert root is not None, (
        "This is impossible, otherwise the previous exception would have been raised."
    )
    root.accept(visitor)
