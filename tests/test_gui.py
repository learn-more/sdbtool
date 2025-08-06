"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Tests for the gui module.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from pathlib import Path
from sdbtool.apphelp import SdbDatabase
from sdbtool.gui import show_gui
import tkinter as tk

TESTDATA_FOLDER = Path(__file__).parent / "data"


def find_item(tree, text, current=None):
    """Helper function to find an item in the Treeview."""
    for item in tree.get_children(current):
        if tree.item(item, "text") == text:
            return item
        tmp = find_item(tree, text, item)  # Recursively search children
        if tmp:
            return tmp
    return None


def test_gui(monkeypatch):
    mainloop_called = False

    def mock_mainloop(self):
        nonlocal mainloop_called
        mainloop_called = True
        treeview = self.children["!treeview"]
        assert treeview is not None
        node = find_item(treeview, "SDB")
        assert node is not None
        assert treeview.item(node, "open") == 1

        node = find_item(treeview, "DATABASE")
        assert node is not None
        assert treeview.item(node, "open") == 1

        # Test a tag where the comment is used as the value
        node = find_item(treeview, "GUEST_TARGET_PLATFORM")
        assert node is not None
        assert treeview.item(node, "values") == ("X86 | ARM64",)

        # Test a tag that is displayed as-is
        node = find_item(treeview, "MATCH_MODE")
        assert node is not None
        assert treeview.item(node, "values") == ("0",)

        # We are done, close the window
        self.destroy()

    monkeypatch.setattr(tk.Tk, "mainloop", mock_mainloop)

    with SdbDatabase(TESTDATA_FOLDER / "all_tagtypes.sdb") as db:
        show_gui(
            db=db,
        )
    assert mainloop_called, "The mainloop was not called, GUI did not launch."
