"""
PROJECT:     sdbtool
LICENSE:     MIT (https://spdx.org/licenses/MIT)
PURPOSE:     Show a simple GUI with the contents of an SDB file.
COPYRIGHT:   Copyright 2025 Mark Jansen <mark.jansen@reactos.org>
"""

from sdbtool.apphelp import (
    TAG_NULL,
    Tags,
    SdbDatabase,
    TagVisitor,
    Tag,
    TagType,
    tag_value_to_string,
)
import tkinter as tk
from tkinter import ttk


class GuiTagVisitor(TagVisitor):
    def __init__(self, treeview):
        """Initialize the GUI tag visitor with a Treeview widget."""
        self._treeview = treeview
        self._nodes = []  # Stack to keep track of nodes

    def visit_list_begin(self, tag: Tag):
        """Visit the beginning of a list tag."""
        parent_node = self._nodes[-1] if self._nodes else ""
        open = tag.tag in (TAG_NULL, Tags.DATABASE)
        node = self._treeview.insert(parent_node, tk.END, text=tag.name, open=open)
        self._nodes.append(node)

    def visit_list_end(self, tag: Tag):
        """Visit the end of a list tag."""
        self._nodes.pop()

    def visit(self, tag: Tag):
        """Visit a tag."""
        parent_node = self._nodes[-1] if self._nodes else ""
        value, comment = (
            tag_value_to_string(tag) if tag.type != TagType.NULL else ("", "")
        )

        if comment:
            value = comment

        self._treeview.insert(parent_node, tk.END, text=tag.name, values=(value,))


def show_gui(db: SdbDatabase):
    window = tk.Tk()
    window.title("SDB Tool GUI")
    window.minsize(800, 600)
    treeview = ttk.Treeview(window, columns=("Value",))
    treeview.heading("#0", text="Tag")
    treeview.heading("Value", text="Value")
    treeview.column("#0", stretch=False, width=300)
    treeview.column("Value", stretch=True)

    verscrlbar = ttk.Scrollbar(window, orient="vertical", command=treeview.yview)

    verscrlbar.pack(side="right", fill="y")
    treeview.configure(yscrollcommand=verscrlbar.set)

    visitor = GuiTagVisitor(treeview)
    root = db.root()
    assert root is not None, (
        "This is impossible, otherwise the previous exception would have been raised."
    )
    root.accept(visitor)
    treeview.pack(fill=tk.BOTH, expand=True)
    window.mainloop()
