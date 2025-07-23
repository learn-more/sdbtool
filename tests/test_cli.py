"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the cli module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from click.testing import CliRunner
import sdbtool.cli
from sdbtool.cli import sdbtool_command


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sdbtool_command, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("sdbtool, version ")


def test_noargs():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sdbtool_command)
        assert result.exit_code == 2
        assert "Usage: sdbtool" in result.output


def test_sdb2xml_command(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sdbtool.cli,
        "sdb2xml_convert",
        lambda input_file, output_stream, exclude_tags, annotations: click.echo(
            f"nop:{exclude_tags}"
        ),
    )
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["sdb2xml", "test.sdb"])
        assert result.exit_code == 0
        assert "nop:[]\n" == result.output
        result = runner.invoke(
            sdbtool_command, ["sdb2xml", "test.sdb", "--exclude", "XXX,YYY"]
        )
        assert result.exit_code == 0
        assert "nop:['XXX', 'YYY']\n" == result.output
        result = runner.invoke(
            sdbtool_command, ["sdb2xml", "test.sdb", "--exclude=auto"]
        )
        assert result.exit_code == 0
        assert "nop:['INDEXES', 'STRINGTABLE']\n" == result.output


def test_sdb2xml_exception(tmp_path, monkeypatch):
    def raise_value_error(*args, **kwargs):
        raise ValueError("Test error")

    monkeypatch.setattr(sdbtool.cli, "sdb2xml_convert", raise_value_error)
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["sdb2xml", "test.sdb"])
        assert result.exit_code == 1
        assert "Error converting SDB to XML" in result.output
        assert "Test error" in result.output


def test_attributes_command(tmp_path, monkeypatch):
    def mock_get_attributes(file_name):
        if file_name == "test2.sdb":
            # Simulate returning a list of attributes
            return ["Test Attribute1", "Test Attribute2"]
        if file_name == "test3.sdb":
            raise ValueError("Test Error")
        return []

    monkeypatch.setattr(sdbtool.cli, "get_attributes", mock_get_attributes)
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test1.sdb", "w") as f:
            f.write("This is a test SDB file.")
        with open("test2.sdb", "w") as f:
            f.write("This is a test SDB file.")
        with open("test3.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(
            sdbtool_command,
            ["attributes", "test1.sdb", "test2.sdb", "test3.sdb"],
        )
        assert result.exit_code == 0
        assert "Attributes for test1.sdb:" in result.output
        assert "No attributes found." in result.output
        assert "Attributes for test2.sdb:" in result.output
        assert "  Test Attribute1" in result.output
        assert "  Test Attribute2" in result.output
        assert "Error getting attributes for test3.sdb: Test Error" in result.output
