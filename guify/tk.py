import inspect
import tkinter as tk
import tkinter.filedialog
from tkinter import ttk

import toolz as tz
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2TkAgg)
import matplotlib.pyplot as plt
import click

from . import types, widgets


STANDARD_MARGIN = (3, 3, 12, 12)

WIDGETS = widgets.WIDGETS_DICT


def format_var_name(var : str) -> str:
    return var


@tz.curry
def guify(function, signature=None, title=None, capitalize=True):
    title = title or function.__name__
    signature = signature or inspect.signature(function)

    class Launch(tk.Tk):
        def __init__(self, params_dict=None):
            super().__init__()
            self.title(title)
            self._prepare_widgets(signature)

            # allow resizing
            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=1)

            self._create_main_frame(signature)

        def _create_main_frame(self, signature):
            main = ttk.Frame(master=self, padding=STANDARD_MARGIN)
            main.grid(row=0, column=0, sticky='nsew')
            self._create_parameters_frame(main, signature)
            self._create_buttons_frame(main)
            main.pack()

        def _create_parameters_frame(self, parent, signature):
            parameters = ttk.Frame(master=parent, padding=STANDARD_MARGIN)
            parameters.grid(sticky='nsew')
            heading = ttk.Label(parameters, text='Parameters')
            heading.grid(column=0, row=0, sticky='n')
            self.widgets = []
            self.parameters = {}
            for i, param in enumerate(signature.parameters.values()):
                widget = self._create_parameter(parent, i, param)
                self.widgets.append(widget)
                self.parameters[param.name] = widget

        def _create_parameter(self, parent_frame, index, param):
            if param.annotation is inspect._empty:
                if param.default is inspect._empty:
                    mesg = ('Guify: unable to infer type for parameter '
                            f'{param.name} of {function.__name__}. ')
                    raise ValueError(mesg)
                else:
                    param_type = type(param.default)
            else:
                param_type = param.annotation
            param_value = (None if param.default is inspect._empty
                           else param.default)
            param_name = format_var_name(param.name)
            param_label = ttk.Label(parent_frame, text=param_name)
            variable = types.VARS[param_type](value=param_value,
                                              name=param_name)
            widget_class = widgets.WIDGETS[param_type]
            widget = widget_class(parent_frame, variable=variable)
            widget.grid(row=index, column=1, sticky='nsew')
            return widget

        def _create_buttons_frame(self, parent):
            buttons = ttk.Frame(master=parent, padding=STANDARD_MARGIN)
            buttons.grid(sticky='nsew')
            actions = [
                ('Load config', self.load_config_file),
                ('Save config', self.save_config_file),
                ('Run', self.run)
            ]
            for col, (action_name, action) in enumerate(actions):
                button = ttk.Button(buttons, text=action_name,
                                    command=action)
                button.grid(row=0, column=col)

        def load_config_file(self):
            filename = tk.filedialog.askopenfilename()
            with open(filename, 'r') as config:
                parameters = json.load(config)
            for param, value in parameters.items():
                self.parameters[param].set(value)

        def save_config_file(self):
            filename = tk.filedialog.askopenfilename()
            with open(filename, 'w') as config:
                json.dump({p: w.get() for p, w in self.parameters.items()},
                          config, indent=2)

        def run(self):
            function(**{param: widget.get()
                     for param, widget in self.parameters.items()})

    def launch_gui():
        app = Launch()
        app.mainloop()

    return launch_gui
