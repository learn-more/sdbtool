'''
PROJECT:     sdb2xml
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Entrypoint of the sdb2xml tool, which converts SDB files to XML format.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
'''
import sys
import sdb2xml.apphelp as apphelp
from base64 import b64encode
from xml.sax.saxutils import escape

INDENT_DEPTH = 2

def tagtype_to_xmltype(tag_type: int) -> str|None:
    switch = {
        apphelp.TAG_TYPE_BYTE: "xs:byte",
        apphelp.TAG_TYPE_WORD: "xs:unsignedShort",
        apphelp.TAG_TYPE_DWORD: "xs:unsignedInt",
        apphelp.TAG_TYPE_QWORD: "xs:unsignedLong",
        apphelp.TAG_TYPE_STRINGREF: "xs:string",
        apphelp.TAG_TYPE_STRING: "xs:string",
        apphelp.TAG_TYPE_BINARY: "xs:base64Binary",
    }
    return switch.get(tag_type, None)

class Xml:
    def __init__(self, stream, name, indent, attrib=None, xmltag=False):
        self._stream = stream
        self.name = name
        self.indent = indent
        self.attrib = attrib or {}
        self._has_children = False
        self._xmltag = xmltag
        self._delay = None
        self._closed = False

    def node(self, name, attrib=None):
        self._has_children = True
        return Xml(self._stream, name, self.indent + 1, attrib)

    def flush(self):
        if self._delay:
            self._stream.write(self._delay)
            self._delay = None

    def write(self, text):
        self.flush()
        self._stream.write(text)

    def close(self):
        assert self._delay is not None, "Xml.close() called when tag has content"
        self._stream.write(" />")
        self._delay = None
        self._closed = True

    def __enter__(self):
        if self._xmltag:
            self.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>')
            self._xmltag = False
        self.write("\n")
        if self.indent:
            self.write(" " * (self.indent*INDENT_DEPTH))
        self.write(f"<{self.name}")
        for key, value in self.attrib.items():
            self.write(f' {key}="{value}"')

        self._delay = ">"
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._closed:
            return
        if self._has_children:
            self.write("\n")
            if self.indent:
                self.write(" " * (self.indent*INDENT_DEPTH))
        self.write(f"</{self.name}>")


def dump_tag(node, tag):
    if tag.type == apphelp.TAG_TYPE_LIST:
        node.flush()
        for childtag in tag.tags():
            attrs = {}
            if childtag.type != apphelp.TAG_TYPE_LIST and childtag.type != apphelp.TAG_TYPE_NULL:
                typename = tagtype_to_xmltype(childtag.type)
                assert typename is not None, f"Unknown tag type: {childtag.tag}"
                attrs["type"] = typename
            with node.node(childtag.name, attrs) as childnode:
                dump_tag(childnode, childtag)
        return

    assert next(tag.tags(), None) is None, f"Tag {tag.name} is not a list but has children"

    if tag.type == apphelp.TAG_TYPE_NULL:
        node.close()
    elif tag.type == apphelp.TAG_TYPE_BYTE:
        node.write("<!-- UNHANDLED BYTE TAG, please report this at https://github.com/learn-more/sdb2xml -->")
    elif tag.type == apphelp.TAG_TYPE_WORD:
        val = tag.as_word()
        node.write(f"{val}")
        if node.name in ("INDEX_TAG", "INDEX_KEY"):
            node.write(f"<!-- {apphelp.tag_to_string(val)} -->")
    elif tag.type == apphelp.TAG_TYPE_DWORD:
        node.write(f"{tag.as_dword()}")
    elif tag.type == apphelp.TAG_TYPE_QWORD:
        node.write(f"{tag.as_qword()}")
    elif tag.type in (apphelp.TAG_TYPE_STRINGREF, apphelp.TAG_TYPE_STRING):
        val = escape(tag.as_string())
        node.write(f"{val}")
    elif tag.type == apphelp.TAG_TYPE_BINARY:
        data = tag.as_bytes()
        if not data:
            node.close()
        else:
            base64_data = b64encode(data).decode('utf-8')
            node.write(base64_data)
    else:
        raise ValueError(f"Unknown tag type: {tag.type} for tag {tag.name}")

def dump_db(path: str):
    with apphelp.SdbDatabase(path, apphelp.PathType.DOS_PATH) as db:
        if not db:
            print(f"Failed to open database at '{path}'")
            return
        attrs = {
            "xmlns:xs": "http://www.w3.org/2001/XMLSchema",
            "path": path,
        }
        sys.stdout.reconfigure(encoding='utf-8')
        with Xml(sys.stdout, "SDB", 0, attrs, xmltag=True) as node:
            dump_tag(node, db.root())

def main():
    for arg in sys.argv[1:]:
        dump_db(arg)

if __name__ == "__main__":
    main()
