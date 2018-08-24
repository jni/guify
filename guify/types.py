from typing import Union as U, Tuple, List, NewType

import tkinter as tk


FilePath = NewType('FilePath', str)
Files = NewType('Files', List[FilePath])
Directory = NewType('Directory', str)
Folder = Directory


class MultiStringVar(tk.Variable):
    _default = []
    def __init__(self, master=None, value=None, name=None):
        super().__init__(self, master, value, name)


VARS = {
    bool: tk.BooleanVar,
    float: tk.DoubleVar,
    str: tk.StringVar,
    int: tk.IntVar,
    FilePath: tk.StringVar,
    Files: MultiStringVar,
    Directory: tk.StringVar,
}
