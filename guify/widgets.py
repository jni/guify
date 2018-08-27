from collections import defaultdict
import tkinter as tk
from tkinter import ttk

from . import types


class FileButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master=master, text='Choose file', **kwargs)
        self.command = self._choose_file

    def _choose_file(self):
        self._variable = tk.filedialog.askopenfilename()

    def get(self):
        return self._variable


class FilesButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master=master, text='Choose file(s)', **kwargs)
        self.command = self._choose_files

    def _choose_files(self):
        self._variable = tk.filedialog.askopenfilenames()

    def get(self):
        return self._variable


class DirectoryButton(ttk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master=master, text='Choose folder', **kwargs)
        self.command = self._choose_folder

    def _choose_folder(self):
        self._variable = tk.filedialog.askdirectory()

    def get(self):
        return self._variable


WIDGETS = defaultdict(ttk.Entry)

WIDGETS.update({
    bool: ttk.Checkbutton,
    types.FilePath: FileButton,
    types.Files: FilesButton,
    types.Directory: DirectoryButton,
})
