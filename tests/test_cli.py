"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the cli module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

import click
from click.testing import CliRunner
from sdbtool.cli import attributes, sdb2xml, info, gui
from sdbtool.cli import sdbtool_command
from sdbtool.cli.types import SDB_DATABASE
from sdbtool.info import DatabaseInformation
from sdbtool.apphelp import SdbDatabase
from uuid import UUID
from pathlib import Path

TESTDATA_FOLDER = Path(__file__).parent / "data"


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
        sdb2xml,
        "sdb2xml_convert",
        lambda db,
        output_stream,
        exclude_tags,
        annotations,
        with_tagid,
        with_tag: click.echo(f"nop:{exclude_tags}"),
    )
    runner = CliRunner()
    db_file = str(TESTDATA_FOLDER / "all_tagtypes.sdb")
    result = runner.invoke(sdbtool_command, ["sdb2xml", db_file])
    assert result.exit_code == 0
    assert "nop:[]\n" == result.output
    result = runner.invoke(
        sdbtool_command, ["sdb2xml", db_file, "--exclude", "XXX,YYY"]
    )
    assert result.exit_code == 0
    assert "nop:['XXX', 'YYY']\n" == result.output
    result = runner.invoke(sdbtool_command, ["sdb2xml", db_file, "--exclude=auto"])
    assert result.exit_code == 0
    assert "nop:['INDEXES', 'STRINGTABLE']\n" == result.output


def test_sdb2xml_exception(tmp_path, monkeypatch):
    def raise_value_error(*args, **kwargs):
        raise ValueError("Test error")

    monkeypatch.setattr(sdb2xml, "sdb2xml_convert", raise_value_error)
    runner = CliRunner()
    db_file = str(TESTDATA_FOLDER / "all_tagtypes.sdb")
    result = runner.invoke(sdbtool_command, ["sdb2xml", db_file])
    assert result.exit_code == 1
    assert "Error converting SDB to XML" in result.output
    assert "Test error" in result.output


def test_sdb2xml_invalid_file(tmp_path, monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test.sdb", "w") as f:
            f.write("")
        result = runner.invoke(sdbtool_command, ["sdb2xml", "test.sdb"])
        assert result.exit_code == 2
        assert "Failed to open database at 'test.sdb'" in result.output
        assert (
            "Invalid value for 'INPUT_FILE': 'test.sdb' is not a valid SDB database:"
            in result.output
        )


def test_attributes_command(tmp_path, monkeypatch):
    def mock_get_attributes(file_name):
        if file_name == "test2.sdb":
            # Simulate returning a list of attributes
            return ["Test Attribute1", "Test Attribute2"]
        if file_name == "test3.sdb":
            raise ValueError("Test Error")
        return []

    monkeypatch.setattr(attributes, "get_attributes", mock_get_attributes)
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


def test_info_command(tmp_path, monkeypatch):
    def mock_get_info(file_name) -> DatabaseInformation:
        if file_name == "test1.sdb":
            return DatabaseInformation(
                Description="Test SDB",
                dwMajor=1,
                dwMinor=0,
                dwFlags=0x1234 | 1,
                Id=UUID(hex="12345678-1234-5678-1234-567812345678"),
                dwRuntimePlatform=2216,
            )
        elif file_name == "test2.sdb":
            return DatabaseInformation(
                Description=None,
                dwMajor=9,
                dwMinor=123123,
                dwFlags=1,
                Id=None,
                dwRuntimePlatform=None,
            )
        raise ValueError("Test Error")

    monkeypatch.setattr(info, "get_info", mock_get_info)
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test1.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["info", "test1.sdb"])
        assert result.exit_code == 0
        assert "Info for test1.sdb:" in result.output
        assert "  Description: Test SDB" in result.output
        assert "  Version: 1.0" in result.output
        assert "  Flags: 0x1235" in result.output
        assert "  ID: 12345678-1234-5678-1234-567812345678" in result.output
        assert "  Runtime Platform: 2216" in result.output
    with runner.isolated_filesystem(tmp_path):
        with open("test2.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["info", "test2.sdb"])
        assert result.exit_code == 0
        assert "Info for test2.sdb:" in result.output
        assert "  Description: N/A" in result.output
        assert "  Version: 9.123123" in result.output
        assert "  Flags: 0x1" in result.output
        assert "  ID: N/A" in result.output
        assert "  Runtime Platform: N/A" in result.output
    with runner.isolated_filesystem(tmp_path):
        with open("test3.sdb", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["info", "test3.sdb"])
        assert result.exit_code == 0
        assert "Error getting info for test3.sdb: Test Error" in result.output


def test_gui_command(tmp_path, monkeypatch):
    def mock_show_gui(input_file):
        if not input_file.name.endswith(".sdb"):
            raise FileNotFoundError(f"File {input_file.name} does not exist.")
        click.echo(f"GUI launched {input_file.name}.")

    monkeypatch.setattr(gui, "show_gui", mock_show_gui)
    # Mock SdbDatabase to always return True for __bool__ to avoid needing a real SDB file
    monkeypatch.setattr(SdbDatabase, "__bool__", lambda self: True)
    runner = CliRunner()
    with runner.isolated_filesystem(tmp_path):
        with open("test.sdb", "w") as f:
            f.write("This is a test SDB file.")
        with open("test.nope", "w") as f:
            f.write("This is a test SDB file.")
        result = runner.invoke(sdbtool_command, ["gui", "test.sdb"])
        assert result.exit_code == 0
        assert "GUI launched test.sdb." in result.output
        result = runner.invoke(sdbtool_command, ["gui", "test.nope"])
        assert result.exit_code == 1
        assert "Error launching GUI: File test.nope does not exist." in result.output


def test_sdb_database_param_type():
    """ Test some click requirements for the SDB_DATABASE type. """
    db_file = TESTDATA_FOLDER / "all_tagtypes.sdb"
    with SdbDatabase(db_file) as db:
        converted = SDB_DATABASE.convert(db, None, None)
        assert converted is db

        other = SDB_DATABASE.convert(db_file, None, None)
        assert isinstance(other, SdbDatabase)
        assert other.path == db_file
        assert other is not db
        other.close()
