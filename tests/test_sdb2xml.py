import io
from click.testing import CliRunner
from sdbtool.cli import cli
from pathlib import Path
from sdbtool import sdb2xml

def test_version():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert result.output.startswith("cli, version ")

def test_databases():
    dbfolder = Path(__file__).parent
    got_files = []
    for dbfile in dbfolder.glob("*.sdb"):
        output = io.StringIO()
        sdb2xml(str(dbfile), output)
        output.seek(0)
        xml_content = output.read()
        expect_result_file = dbfolder / (dbfile.name + ".xml")
        with expect_result_file.open("r", encoding="utf-8") as f:
            expected_content = f.read()
        assert xml_content == expected_content
        got_files.append(dbfile.name)

    expected_files = ['game.sdb', 'shim_db.sdb', 'test.sdb', 'testdb.sdb']
    expected_files.sort()
    got_files.sort()
    assert got_files == expected_files, f"Expected files: {expected_files}, got: {got_files}"
