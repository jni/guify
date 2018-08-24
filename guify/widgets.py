from collections import defaultdict
from tkinter import ttk

from . import types


class FileButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        self.command = 

    def _choose_file(self):
        self._variable


WIDGETS = defaultdict(ttk.Entry)

WIDGETS.update({
    bool: ttk.Checkbutton,
    types.FilePath: FileButton,
    types.Files: FilesButton,
    types.Directory: DirectoryButton,
})
