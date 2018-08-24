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
            for i, param in enumerate(signature.parameters.values()):
                self.widgets.append(self._create_parameter(parent, i, param))

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

        def _create_parameters_frame(self, parent):

            for i, param in enumerate(self.parameters, start=1):
                param_label = ttk.Label(parameters, text=param._name)
                param_label.grid(row=i, column=0, sticky='nsew')
                if type(param) == tk.BooleanVar:
                    param_entry = ttk.Checkbutton(parameters, variable=param)
                elif hasattr(param, '_choices'):
                    param_entry = ttk.OptionMenu(parameters, param, param.get(),
                                                 *param._choices.keys())
                else:
                    param_entry = ttk.Entry(parameters, textvariable=param)
                param_entry.grid(row=i, column=1, sticky='nsew')

        def _create_buttons_frame(self, parent):
            buttons = ttk.Frame(master=parent, padding=STANDARD_MARGIN)
            buttons.grid(sticky='nsew')
            actions = [
                ('Choose config', self.choose_config_file),
                ('Choose files', self.choose_input_files),
                ('Choose output folder', self.choose_output_folder),
                ('Run', lambda: asyncio.ensure_future(self.run()))
            ]
            for col, (action_name, action) in enumerate(actions):
                button = ttk.Button(buttons, text=action_name,
                                    command=action)
                button.grid(row=0, column=col)

        def parameter_config(self, params_dict):
            """Set parameter values from a config dictionary."""
            if isinstance(params_dict, str):
                if params_dict.startswith('{'):  # JSON string
                    params_dict = json.loads(params_dict)
                else:  # config file
                    with open(params_dict) as params_fin:
                        params_dict = json.load(params_fin)
                self.params_dict.update(params_dict)
            name2param = {p._name.lower(): p for p in self.parameters}
            for param, value in self.params_dict.items():
                if param.lower() in name2param:
                    name2param[param].set(value)
                    params_dict.pop(param)
            for param, value in params_dict.copy().items():
                if param.lower() == 'input files':
                    self.input_files = value
                    params_dict.pop(param)
                elif param.lower() == 'output folder':
                    self.output_folder = Path(os.path.expanduser(value))
                    params_dict.pop(param)
                elif param.lower() == 'version':
                    print(f'Parameter file version: {params_dict.pop(param)}')
            for param in params_dict:
                print(f'Parameter not recognised: {param}')

        def save_parameters(self, filename=None):
            out = {p._name.lower(): p.get() for p in self.parameters}
            out['input files'] = self.input_files
            out['output folder'] = str(self.output_folder)
            out['version'] = __version__
            if filename is None:
                return json.dumps(out)
            attempt = 0
            base, ext = os.path.splitext(filename)
            while os.path.exists(filename):
                filename = f'{base} ({attempt}){ext}'
                attempt += 1
            with open(filename, mode='wt') as fout:
                json.dump(out, fout, indent=2)

        def choose_config_file(self):
            config_file = tk.filedialog.askopenfilename()
            self.parameter_config(config_file)

        def choose_input_files(self):
            self.input_files = tk.filedialog.askopenfilenames()
            if len(self.input_files) > 0 and self.output_folder is None:
                self.output_folder = Path(os.path.dirname(self.input_files[0]))

        def choose_output_folder(self):
            self.output_folder = Path(
                    tk.filedialog.askdirectory(initialdir=self.output_folder))

        def make_figure_window(self):
            self.figure_window = tk.Toplevel(self)
            self.figure_window.wm_title('Preview')
            screen_dpi = self.figure_window.winfo_fpixels('1i')
            screen_width = self.figure_window.winfo_screenwidth()  # in pixels
            figure_width = screen_width / 2 / screen_dpi
            figure_height = 0.75 * figure_width
            self.figure = Figure(figsize=(figure_width, figure_height),
                                 dpi=screen_dpi)
            ax0 = self.figure.add_subplot(221)
            axes = [self.figure.add_subplot(220 + i, sharex=ax0, sharey=ax0)
                    for i in range(2, 5)]
            self.axes = np.array([ax0] + axes)
            canvas = FigureCanvasTkAgg(self.figure, master=self.figure_window)
            canvas.show()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            toolbar = NavigationToolbar2TkAgg(canvas, self.figure_window)
            toolbar.update()
            canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        async def run(self):
            print('Input files:')
            for file in self.input_files:
                print('  ', file)
            print('Parameters:')
            for param in self.parameters:
                p = param.get()
                print('  ', param, type(p), p)
            print('Output:', self.output_folder)
            save_skeleton = ('' if not self.save_skeleton_plots.get() else
                             self.skeleton_plot_prefix.get())
            images_iterator = pipe.process_images(
                    self.input_files, self.image_format.get(),
                    self.threshold_radius.get(),
                    self.smooth_radius.get(),
                    self.brightness_offset.get(),
                    self.scale_metadata_path.get(),
                    crop_radius=self.crop_radius.get(),
                    smooth_method=self.smooth_method.get())
            if self.preview_skeleton_plots.get():
                self.make_figure_window()
            elif self.save_skeleton_plots.get():
                self.figure = plt.figure()
                ax0 = self.figure.add_subplot(221)
                axes = [self.figure.add_subplot(220 + i, sharex=ax0, sharey=ax0)
                        for i in range(2, 5)]
                self.axes = np.array([ax0] + axes)
            self.save_parameters(self.output_folder / 'skan-config.json')
            for i, result in enumerate(images_iterator):
                if i < len(self.input_files):
                    filename, image, thresholded, skeleton, framedata = result
                    if save_skeleton:
                        for ax in self.axes:
                            ax.clear()
                        w, h = draw.pixel_perfect_figsize(image)
                        self.figure.set_size_inches(4*w, 4*h)
                        draw.pipeline_plot(image, thresholded, skeleton, framedata,
                                           figure=self.figure, axes=self.axes)
                        output_basename = (save_skeleton +
                                           os.path.basename(
                                               os.path.splitext(filename)[0]) +
                                           '.png')
                        output_filename = str(self.output_folder / output_basename)
                        self.figure.savefig(output_filename)
                    if self.preview_skeleton_plots.get():
                        self.figure.canvas.draw_idle()
                else:
                    result_full, result_image = result
                    result_filtered = result_full[(result_full['mean shape index']>0.125) &
                                                  (result_full['mean shape index']<0.625) &
                                                  (result_full['branch-type'] == 2) &
                                                  (result_full['euclidean-distance']>0)]
                    ridgeydata = result_filtered.groupby('filename')[['filename','branch-distance','scale','euclidean-distance','squiggle','mean shape index']].mean()
                    io.write_excel(str(self.output_folder /
                                       self.output_filename.get()),
                                   branches=result_full,
                                   images=result_image,
                                   filtered=ridgeydata,
                                   parameters=json.loads(self.save_parameters()))
    def launch_gui():
        params = json.load(open(config)) if config else None
        app = Launch(params)
        loop = asyncio.get_event_loop()
        tk_update(loop, app)
        loop.run_forever()
        

    function.launch_gui = launch_gui



def tk_update(loop, app):
    try:
        app.update()
    except tkinter.TclError:
        loop.stop()
        return
    loop.call_later(.01, tk_update, loop, app)


@click.command()
@click.option('-c', '--config', default='',
              help='JSON configuration file.')
def launch(config):
    params = json.load(open(config)) if config else None
    app = Launch(params)
    loop = asyncio.get_event_loop()
    tk_update(loop, app)
    loop.run_forever()
