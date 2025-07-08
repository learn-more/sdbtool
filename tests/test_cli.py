"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the cli module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from click.testing import CliRunner
from sdbtool.cli import sdbtool_command


def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(sdbtool_command, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("sdbtool, version ")
