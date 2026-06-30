# sdbtool

A tool for converting Microsoft Application Compatibility Database (SDB) files to XML format.

--------

[![PyPI - Version](https://img.shields.io/pypi/v/sdbtool)](https://pypi.org/project/sdbtool/)
[![PyPI - License](https://img.shields.io/pypi/l/sdbtool)](https://pypi.org/project/sdbtool/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sdbtool)](https://pypi.org/project/sdbtool/)\
[![CI](https://github.com/learn-more/sdbtool/actions/workflows/python-test.yml/badge.svg?event=push)](https://github.com/learn-more/sdbtool/actions/workflows/python-test.yml)
[![Publish Python Package](https://github.com/learn-more/sdbtool/actions/workflows/python-publish.yml/badge.svg)](https://github.com/learn-more/sdbtool/actions/workflows/python-publish.yml)
[![codecov](https://codecov.io/gh/learn-more/sdbtool/graph/badge.svg?token=Z476TDD3B2)](https://codecov.io/gh/learn-more/sdbtool)



## Table of Contents

1. [Features](#features)
1. [Getting Started](#getting-started)
1. [Contributing](#contributing)

## Features<a id="features"></a>

- Parses SDB files used by Windows for application compatibility.
- Converts SDB data into readable XML or JSON format.
- Dump file attributes in SDB-recognizable format
- Useful for analysis, migration, or documentation.
- Pure Python and cross-platform - no native `apphelp.dll` dependency.


## Getting Started<a id="getting-started"></a>

### Installation

Sdbtool is available as [`sdbtool`](https://pypi.org/project/sdbtool/) on PyPI.

Invoke sdbtool directly with [`uvx`](https://docs.astral.sh/uv/):

```shell
uvx sdbtool sdb2xml your.sdb                        # Convert the file 'your.sdb' to xml, and print it to the console
uvx sdbtool sdb2xml your.sdb --output your.xml      # Convert the file 'your.sdb' to xml, and write it to 'your.xml'
uvx sdbtool sdb2json your.sdb                       # Convert the file 'your.sdb' to json, and print it to the console
uvx sdbtool sdb2json your.sdb --output your.json    # Convert the file 'your.sdb' to json, and write it to 'your.json'
uvx sdbtool sdb2xml old.sdb --target-os 0501        # Resolve tag names as of Windows XP (for older databases)
uvx sdbtool attributes your.exe                     # Show the file attributes as recognized by apphelp in an XML-friendly format
uvx sdbtool info your.sdb                           # Show some details about the SDB file (version, description, ...)
```

### Tag names and `--target-os`

Tag names are not constant across Windows versions: some are renamed (e.g. `OS_PLATFORM`
became `GUEST_TARGET_PLATFORM`) and some are dropped (e.g. `OS_SKU` exists on XP but not on
Windows 11). `sdb2xml` / `sdb2json` therefore accept `--target-os <VERSION>` to resolve names as
of a particular Windows release; without it, names are resolved against the newest known table.
An unknown tag is rendered as `InvalidTag_0xXXXX`.

Or install sdbtool with `uv` (recommended), `pip`, or `pipx`:

```shell
# With uv.
uv tool install sdbtool@latest  # Install sdbtool globally.

# With pip.
pip install sdbtool

# With pipx.
pipx install sdbtool
```

Updating an installed sdbtool to the latest version with `uv`:
```shell
# With uv.
uv tool upgrade sdbtool

# With pip.
pip install --upgrade sdbtool

# With pipx.
pipx upgrade sdbtool
```


## Contributing<a id="contributing"></a>

Contributions are welcome! Please open issues or submit pull requests.

### Regenerating the tag tables

The tag-id → name tables live in [`sdbtool/apphelp/tags/tags.json`](sdbtool/apphelp/tags/tags.json)
as a `base` table plus per-version `add` / `override` / `remove` deltas. They are produced offline
from every `apphelp.dll` version by [`tools/generate_tags.py`](tools/generate_tags.py), which calls
the DLL's `SdbTagToString` export.

Each DLL is read with **[Speakeasy](https://github.com/mandiant/speakeasy)**:
it parses and emulates the PE regardless of bitness, so one 64-bit run handles the x86 (XP / 2003)
DLLs as well as DLLs the OS refuses to load natively. Speakeasy lives in the optional `gen` dependency group.

```shell
uv run --group gen python tools/generate_tags.py --data-dir path\to\apphelp\dlls
```

The data directory is expected to contain `<version>/<arch>/apphelp.dll` files (e.g.
`0501/x86/apphelp.dll`, `0A00-26200/x64-64/apphelp.dll`); add more versions by dropping their
`apphelp.dll` in and regenerating.
