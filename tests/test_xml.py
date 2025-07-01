"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     tests for the XmlWriter class.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.xml import XmlWriter
import io


def test_xml_writer():
    stream = io.StringIO()
    writer = XmlWriter(stream)

    writer.write_xml_declaration()
    writer.open("root", {"attr": "value&tag<test>"})
    writer.open("child")
    writer.write("Content&tag<test>")
    writer.close("child")
    writer.empty_tag("empty")
    writer.write_comment("This is a comment with special characters: & < >")
    writer.close("root")

    expected_output = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n<root attr="value&amp;tag&lt;test&gt;">\n  <child>Content&amp;tag&lt;test&gt;</child>\n  <empty /><!-- This is a comment with special characters: &amp; &lt; &gt; -->\n</root>'
    assert stream.getvalue() == expected_output
