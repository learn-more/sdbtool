# sdbtool

A tool for converting Microsoft Application Compatibility Database (SDB) files to XML format.

## Table of Contents

1. [Features](#features)
1. [Getting Started](#getting-started)
1. [Contributing](#contributing)
1. [License](#license)

## Features<a id="features"></a>

- Parses SDB files used by Windows for application compatibility.
- Converts SDB data into readable XML.
- Dump file attributes in SDB-recognizable format
- Useful for analysis, migration, or documentation.


## Getting Started<a id="getting-started"></a>

### Installation

Sdbtool is available as [`sdbtool`](https://pypi.org/project/sdbtool/) on PyPI.

Invoke sdbtool directly with [`uvx`](https://docs.astral.sh/uv/):

```shell
uvx sdbtool sdb2xml your.sdb                    # Convert the file 'your.sdb' to xml, and print it to the console
uvx sdbtool sdb2xml your.sdb --output your.xml  # Convert the file 'your.sdb' to xml, and write it to 'your.xml'
uvx sdbtool attributes your.exe                 # Show the file attributes as recognized by apphelp in an XML-friendly format
```

Or install sdbtool with `uv` (recommended), `pip`, or `pipx`:

```shell
# With uv.
uv tool install sdbtool@latest  # Install sdbtool globally.

# With pip.
pip install sdbtool

# With pipx.
pipx install sdbtool
```

## Contributing<a id="contributing"></a>

Contributions are welcome! Please open issues or submit pull requests.

## License<a id="license"></a>

This project is licensed under the MIT License.
