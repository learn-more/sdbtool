"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Convert SDB files to JSON format.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import (
    SdbDatabase,
    TagVisitor,
    TagType,
    Tag,
    tag_value_to_string,
)
import json


def tagtype_to_jsontype(tag_type: TagType) -> str | None:
    tagtype_map = {
        TagType.BYTE: "byte",
        TagType.WORD: "word",
        TagType.DWORD: "dword",
        TagType.QWORD: "qword",
        TagType.STRINGREF: "string",
        TagType.STRING: "string",
        TagType.BINARY: "binary",
    }
    return tagtype_map.get(tag_type, None)


class JsonTagVisitor(TagVisitor):
    def __init__(
        self,
        input_filename: str,
        with_annotations: bool,
        with_tagid: bool,
        with_tag: bool,
    ):
        self._with_annotations = with_annotations
        self._with_tagid = with_tagid
        self._with_tag = with_tag
        self._root_meta: dict = {"file": input_filename}
        self._top_children: list = []
        self._stack: list[dict] = [{"children": self._top_children}]

    def visit_list_begin(self, tag: Tag):
        if tag.tag_id == 0:
            # Root SDB node — its attributes go on the root dict itself
            if self._with_tagid:
                self._root_meta["tagid"] = tag.tag_id
            if self._with_tag:
                self._root_meta["tag_num"] = f"0x{tag.tag:x}"
            return

        node: dict = {"tag": tag.name}
        if self._with_tagid:
            node["tagid"] = tag.tag_id
        if self._with_tag:
            node["tag_num"] = f"0x{tag.tag:x}"
        node["children"] = []
        self._stack[-1]["children"].append(node)
        self._stack.append(node)

    def visit_list_end(self, tag: Tag):
        if tag.tag_id == 0:
            return
        self._stack.pop()

    def visit(self, tag: Tag):
        if tag.type == TagType.NULL:
            node: dict = {"tag": tag.name, "type": "null"}
            if self._with_tagid:
                node["tagid"] = tag.tag_id
            if self._with_tag:
                node["tag_num"] = f"0x{tag.tag:x}"
            self._stack[-1]["children"].append(node)
            return

        typename = tagtype_to_jsontype(tag.type)
        if typename is None:
            raise ValueError(
                f"Unknown json tag type: {tag.type.name} for tag {tag.name}"
            )

        value, comment = tag_value_to_string(tag)
        node = {"tag": tag.name, "type": typename, "value": value}
        if self._with_tagid:
            node["tagid"] = tag.tag_id
        if self._with_tag:
            node["tag_num"] = f"0x{tag.tag:x}"
        if self._with_annotations and comment is not None:
            node["comment"] = comment
        self._stack[-1]["children"].append(node)

    def result(self) -> dict:
        return {**self._root_meta, "children": self._top_children}


class _FilteringVisitor(TagVisitor):
    """Wraps JsonTagVisitor to apply tag exclusion."""

    def __init__(self, inner: JsonTagVisitor, exclude_tags: list[str]):
        self._inner = inner
        self._exclude_tags = exclude_tags
        self._skip_depth = 0

    def visit_list_begin(self, tag: Tag):
        if tag.name in self._exclude_tags:
            self._skip_depth += 1
        if self._skip_depth > 0:
            return
        self._inner.visit_list_begin(tag)

    def visit_list_end(self, tag: Tag):
        if self._skip_depth > 0:
            if tag.name in self._exclude_tags:
                self._skip_depth -= 1
            return
        self._inner.visit_list_end(tag)

    def visit(self, tag: Tag):
        if self._skip_depth > 0:
            return
        if tag.name in self._exclude_tags:
            return
        self._inner.visit(tag)


def convert(
    db: SdbDatabase,
    output_stream,
    exclude_tags: list[str],
    with_annotations: bool,
    with_tagid: bool,
    with_tag: bool,
):
    visitor = JsonTagVisitor(
        db.name,
        with_annotations=with_annotations,
        with_tagid=with_tagid,
        with_tag=with_tag,
    )
    root = db.root()
    assert root is not None, (
        "This is impossible, otherwise the previous exception would have been raised."
    )
    root.accept(_FilteringVisitor(visitor, exclude_tags))
    json.dump(visitor.result(), output_stream, indent=2)
    output_stream.write("\n")
