# sdb2xml

A tool for converting Microsoft Application Compatibility Database (SDB) files to XML format.

## Features

- Parses SDB files used by Windows for application compatibility.
- Converts SDB data into readable XML.
- Useful for analysis, migration, or documentation.

## Requirements

- Python 3.10+

## Usage

### With uv (recommended)

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Use `uvx sdb2xml` to run this tool, or `uv tool install sdb2xml` to install it.

For help, run:
```bash
uvx sdb2xml --help
```
or when installed:
```bash
sdb2xml --help
```

### With pip

Install this tool using `pip`:
```bash
pip install sdb2xml
```

For help, run:
```bash
sdb2xml --help
```
You can also use:
```bash
python -m sdb2xml --help
```

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.
