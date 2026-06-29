"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Offline generator for the version-aware SDB tag tables.
COPYRIGHT:   Copyright 2026 Mark Jansen <mark.jansen@reactos.org>

This script is NOT part of the installed sdbtool package -- it lives outside the
``sdbtool`` package on purpose so it never ends up in the wheel/sdist. It is only
relevant to the author when (re)generating ``sdbtool/apphelp/tags/tags.json``.

It extracts the tag table from every ``apphelp.dll`` it can find under a data
directory (one per Windows version) by calling the DLL's ``SdbTagToString`` export
for a set of candidate tag ids.

Every DLL is read with **Speakeasy** (Mandiant's emulator): it parses and emulates
the PE itself, irrespective of host/DLL bitness, so a single 64-bit run handles the
x86 (XP / 2003) DLLs as well as DLLs the OS refuses to load natively (some Win7/8.1
``apphelp.dll`` fail a real ``LoadLibrary`` with ``WinError 182``). Speakeasy lives
in the optional ``gen`` dependency group: ``uv sync --group gen``.

The per-version tables are then stored as a compact *base + deltas* document: the
newest table is the ``base`` and every other version is expressed as the
``add`` / ``override`` / ``remove`` it applies to that base.

Usage::

    uv run --group gen python tools/generate_tags.py --data-dir R:\\src\\shimextract\\data
"""

from __future__ import annotations

import argparse
import copy
import json
import multiprocessing
import os
import sys
from pathlib import Path

# Candidate tag ids. A TAG is a type nibble (0x1000..0x9000) plus a 12-bit index.
# Real tags only ever use a small slice of that index space: the regular tags sit
# in 0x000..0x1FF and a few reserved ones (stringtable / indexes) in 0x800..0x8FF.
# Scanning just those (instead of the full 0x000..0xFFF) keeps the emulated probing
# tractable while covering every tag seen across all shipped Windows versions.
_INDEX_SEGMENTS = ((0x000, 0x200), (0x800, 0x900))


def candidate_tags() -> list[int]:
    """The tag ids probed with ``SdbTagToString``."""
    tags = []
    for nibble in range(0x1, 0xA):
        base = nibble << 12
        for lo, hi in _INDEX_SEGMENTS:
            tags.extend(base | idx for idx in range(lo, hi))
    return tags


def version_sort_key(version_dir: str) -> tuple[int, int]:
    """Sort key for a data-dir version name like ``0501`` or ``0A00-26200``.

    The leading field is the OS major/minor as 4 hex digits; an optional
    ``-<build>`` suffix (decimal) disambiguates Win10/11 releases.
    """
    head, _, tail = version_dir.partition("-")
    major_minor = int(head, 16)
    build = int(tail) if tail.isdigit() else 0
    return (major_minor, build)


def load_speakeasy():
    """Import Speakeasy with the noisy unicorn/pkg_resources warnings silenced."""
    import warnings

    warnings.filterwarnings("ignore", category=SyntaxWarning)
    warnings.filterwarnings("ignore", message=r".*pkg_resources is deprecated.*")
    try:
        import speakeasy
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "speakeasy not available; install the optional generator deps with"
            " `uv sync --group gen`"
        ) from exc
    return speakeasy


def _speakeasy_config(speakeasy) -> dict:
    """Speakeasy's default config with the post-run string rescan disabled.

    We issue one emulated call per candidate tag (thousands of runs) and never use
    the scanned strings, so leaving the analysis on would dominate the runtime.
    """
    cfg_path = os.path.join(
        os.path.dirname(speakeasy.__file__), "configs", "default.json"
    )
    with open(cfg_path, encoding="utf-8") as fp:
        cfg = json.load(fp)
    cfg.setdefault("analysis", {})["strings"] = False
    return cfg


def extract_dll(speakeasy, cfg: dict, dll: Path) -> dict[int, str]:
    """Emulate ``dll`` and return ``{tag_id: name}`` from ``SdbTagToString``."""
    se = speakeasy.Speakeasy(config=copy.deepcopy(cfg))
    module = se.load_module(str(dll))
    ret_reg = "rax" if module.get_ptr_size() == 8 else "eax"

    func_addr = module.get_export_by_name("SdbTagToString")
    if not func_addr:
        raise RuntimeError(f"{dll.name}: no SdbTagToString export")

    out: dict[int, str] = {}
    for tag in candidate_tags():
        se.call(func_addr, [tag])
        ptr = se.reg_read(ret_reg)
        if not ptr:
            continue
        name = se.read_mem_string(ptr, 2, max_chars=128)  # width 2 = UTF-16
        if name and name != "InvalidTag":
            out[tag] = name
    return out


def discover(data_dir: Path) -> dict[str, list[Path]]:
    """Map each version-dir name to the apphelp.dll(s) found beneath it."""
    found: dict[str, list[Path]] = {}
    for dll in sorted(data_dir.glob("*/**/apphelp.dll")):
        version = dll.relative_to(data_dir).parts[0]
        found.setdefault(version, []).append(dll)
    return found


def _dll_worker(version: str, dll: str) -> tuple:
    """Process-pool task: extract one DLL's table in its own fresh Speakeasy.

    Exactly one DLL per task, so each emulation gets a pristine subprocess (Speakeasy
    keeps process-global state). Returns ``(version, dll, table, None)`` on success or
    ``(version, dll, None, error)``. Top-level + picklable so the spawn pool can ship
    it.
    """
    try:
        speakeasy = load_speakeasy()
        cfg = _speakeasy_config(speakeasy)
    except BaseException as exc:  # noqa: BLE001 - SystemExit from load too
        return (version, dll, None, f"speakeasy unavailable: {exc}")
    try:
        return (version, dll, extract_dll(speakeasy, cfg, Path(dll)), None)
    except Exception as exc:  # noqa: BLE001
        return (version, dll, None, str(exc))


def build_tables(data_dir: Path, jobs: int) -> list[tuple[str, dict[int, str]]]:
    """Extract all version tables in parallel, ordered oldest -> newest."""
    found = discover(data_dir)
    versions = sorted(found, key=version_sort_key)

    # One task == one DLL == one fresh subprocess. Speakeasy keeps process-global
    # state, so a worker must never emulate a second DLL (see shimextract emulate.py).
    # multiprocessing.Pool's maxtasksperchild=1 enforces that on every supported
    # Python (unlike ProcessPoolExecutor.max_tasks_per_child, 3.11+). Spawn is
    # required: maxtasksperchild is incompatible with the fork start method.
    # A version may have several candidate DLLs; we try its first, and only fall back
    # to the next (in a later round, still a fresh process) if that one failed.
    ctx = multiprocessing.get_context("spawn")
    nworkers = max(1, min(jobs, len(versions)))
    pending = {v: [str(p) for p in found[v]] for v in versions}

    results: dict[str, dict[int, str]] = {}
    with ctx.Pool(processes=nworkers, maxtasksperchild=1) as pool:
        while pending:
            batch = [(v, dlls[0]) for v, dlls in pending.items()]
            retry: dict[str, list[str]] = {}
            for version, dll, table, err in pool.starmap(_dll_worker, batch):
                if table is not None:
                    rel = Path(dll).relative_to(data_dir)
                    print(f"  + {version}: {len(table)} tags  ({rel})")
                    results[version] = table
                elif pending[version][1:]:
                    retry[version] = pending[version][1:]
                else:
                    print(f"  ! {version}: skipped ({err})", file=sys.stderr)
            pending = retry

    return [(v, results[v]) for v in versions if v in results]


def make_document(tables: list[tuple[str, dict[int, str]]]) -> dict:
    """Encode the per-version tables as a base + deltas document (newest = base)."""
    base_version, base = tables[-1]

    def hexkey(tag: int) -> str:
        return f"0x{tag:04x}"

    versions = []
    for name, table in tables:
        add = {hexkey(t): n for t, n in table.items() if t not in base}
        override = {
            hexkey(t): n for t, n in table.items() if t in base and base[t] != n
        }
        remove = [hexkey(t) for t in base if t not in table]
        versions.append(
            {
                "name": name,
                "version": version_sort_key(name)[0],
                "build": version_sort_key(name)[1],
                "add": dict(sorted(add.items())),
                "override": dict(sorted(override.items())),
                "remove": sorted(remove),
            }
        )

    return {
        "base_version": base_version,
        "base": {hexkey(t): base[t] for t in sorted(base)},
        "versions": versions,
    }


def report_differences(tables: list[tuple[str, dict[int, str]]]) -> None:
    """Print tags that change name across versions (renames / drops), for auditing."""
    all_ids = sorted({t for _, table in tables for t in table})
    print("\nCross-version name changes:")
    any_diff = False
    for tag in all_ids:
        seen = [(name, table.get(tag, "-")) for name, table in tables]
        names = {n for _, n in seen if n != "-"}
        if len(names) > 1:
            any_diff = True
            trail = ", ".join(f"{name}={value}" for name, value in seen)
            print(f"  0x{tag:04x}: {trail}")
    if not any_diff:
        print("  (none)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(r"R:\src\shimextract\data"),
        help="Directory containing <version>/<arch>/apphelp.dll files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "sdbtool"
        / "apphelp"
        / "tags"
        / "tags.json",
        help="Path of the tags.json data file to write.",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=os.cpu_count() or 4,
        help="Parallel Speakeasy workers (one DLL each) [default: CPU count].",
    )
    args = parser.parse_args()

    print(f"Scanning {args.data_dir} for apphelp.dll ...")
    tables = build_tables(args.data_dir, args.jobs)
    if not tables:
        print("No tables extracted.", file=sys.stderr)
        return 1

    report_differences(tables)

    document = make_document(tables)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as fp:
        json.dump(document, fp, indent=2)
        fp.write("\n")

    total = len(document["base"])
    print(
        f"\nWrote {args.output} "
        f"({len(tables)} versions, base '{document['base_version']}' = {total} tags)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
