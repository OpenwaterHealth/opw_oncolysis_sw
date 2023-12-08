"""
GUI for the Oncolysis Controller

module containing the main application window class and functions
"""
import tkinter as tk
import os
import logging
from oncolysis_ctrl import controller, config
from tkinter import font, ttk, messagebox
import traceback
import idlelib.tooltip as tooltip
import numpy as np

HERE = os.path.dirname(__file__)
logger = logging.getLogger("oc.app")

constants = config.constants
logger.info(f'Using configuration "{config.config_id}"')


def config_time(t):
    """
    Convert time in seconds to a string in the format HH:MM:SS

    :param t: time in seconds
    :return: time string
    """
    return (f'{int(t / 3600):01d}:' if t >= 3600 else '') + f'{int((t % 3600) / 60):02d}:{int((t % 60)):02d}'


class App(tk.Frame):
    """
    The main application window. 

    This is the first window that appears when the application is launched.

    :param root: The root window
    :param simulate: If True, the application will run in simulation mode, which will not communicate with the hardware
    :param config_ids: A list of configuration IDs
    :param frequencies: A list of frequencies to treat
    :param durations: A list of treatment durations
    :param duration: The default treatment duration
    :param burst_lengths: A list of burst lengths
    :param burst_length: The default burst length
    :param duty_cycles: A list of duty cycles
    :param duty_cycle: The default duty cycle
    :param power_modes: A list of power modes
    :param power_mode: The default power mode
    :param power_settings: A dictionary of power settings
    :param voltage_calibration: A dictionary of voltage calibration values
    :param amplifier_gain: The amplifier gain
    """
    def __init__(self, root, 
                 simulate=False, 
                 config_ids=config.CONFIG_IDS, 
                 frequencies=constants.FREQUENCIES_KHZ,
                 durations=constants.DURATIONS_S, duration=constants.DURATION_S, 
                 burst_lengths=constants.BURST_LENGTHS, burst_length=constants.BURST_LENGTH,
                 duty_cycles=constants.BURST_DUTY_CYCLES, duty_cycle=constants.BURST_DUTY_CYCLE,
                 power_modes=constants.POWER_MODES, power_mode=constants.POWER_MODE,
                 power_settings=constants.POWER_SETTINGS, 
                 voltage_calibration=constants.CALIB,
                 amplifier_gain=constants.AMPLIFIER_GAIN): 
        super().__init__(root)
        self.top = self.winfo_toplevel()
        config_id = config.get_config_id()
        if simulate:
            self.top.title(f'OpenWater Oncolysis Controller ({config_id}, SIMULATE MODE)')
        else:
            self.top.title(f'OpenWater Oncolysis Controller ({config_id})')

        self.bigfont = font.Font(size=20, weight=font.BOLD)
        self.mediumfont = font.Font(size=16, weight=font.BOLD)
        self.smallfont = font.Font(size=12, weight=font.BOLD)
        self.monofont = font.Font(family='MS Gothic', size=12, weight=font.BOLD)
        root.option_add('*font', self.mediumfont)
        default_font = font.nametofont("TkTextFont")
        default_icon_font = font.nametofont("TkIconFont")
        default_font.configure(size=16)
        default_icon_font.configure(size=22)
        self.root = root
        self.frequencies = frequencies

        frowidx = 0
        self.configure_frame = tk.LabelFrame(self, text='Configuration', font=self.smallfont,
                                             padx=10, pady=5)
        config_id = config.get_config_id()
        if config_id in config.CONFIG_IDS:
            config_name = config.CONFIG_NAMES[config.CONFIG_IDS.index(config_id)]
        else:
            config_name = config.CONFIG_NAMES[0]
        self.config_names = tuple(config.CONFIG_NAMES[config.CONFIG_IDS.index(config_id)] for config_id in config_ids)
        self.config_name = tk.StringVar(value=f'{config_name}')
        self.config_select = tk.OptionMenu(self.configure_frame,
                                           self.config_name,
                                           *self.config_names,
                                           command=self.load_config)
        self.config_select.configure(font=self.smallfont)
        if len(config_ids) < 2:
            self.config_select.configure(state='disabled')
        self.config_select.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.config_select.configure(width=24, height=2, anchor='w', pady=4)
        self.simulate_var = tk.IntVar(value=int(simulate))
        self.simulate_checkbox = tk.Checkbutton(self.configure_frame,
                                                text='Simulate',
                                                indicatoron=False,
                                                variable=self.simulate_var,
                                                onvalue=1,
                                                offvalue=0,
                                                command=self.set_simulate,
                                                font=self.smallfont)
        self.simulate_checkbox.pack(side=tk.LEFT, expand=False, fill=tk.BOTH, pady=2)
        self.simulate_checkbox.configure(width=6, height=2, anchor='center', pady=0, padx=10)
        self.configure_frame.grid(row=frowidx, column=0, sticky=tk.E+tk.W, padx=10)
        self.grid_rowconfigure(frowidx, weight=1)
        frowidx += 1

        self.connect_frame = tk.Frame(self, padx=10, pady=10)
        self.toggle_connect_button = tk.Button(self.connect_frame, text='Connect', command=self.toggle_connect,
                                               font=self.mediumfont)
        self.toggle_connect_button.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.connect_frame.grid(row=frowidx, column=0, sticky=tk.E+tk.W)
        self.grid_rowconfigure(frowidx, weight=1)
        frowidx += 1

        self.param_frame = tk.Frame(self, padx=10, pady=10)
        rowidx = 0
        self.root = root
        # Create Frequency Selector
        self.freqsel_frame = tk.LabelFrame(self.param_frame, text='Frequencies to Treat (kHz)', font=self.smallfont,
                                           padx=5, pady=5)
        for i in range(2):
            self.freqsel_frame.rowconfigure(i, weight=1)
        self.frequency_data = {}
        for i, f in enumerate(self.frequencies):
            d = {}
            d['value'] = f
            d['var'] = tk.IntVar()
            d['command'] = lambda freq=f: self.set_frequencies(freq)
            d['checkbox'] = tk.Checkbutton(self.freqsel_frame,
                                           text=f'{f}',
                                           indicatoron=False,
                                           command=d['command'],
                                           variable=d['var'],
                                           onvalue=1,
                                           offvalue=0,
                                           width=4,
                                           font=self.bigfont)
            d['checkbox'].grid(row=0, column=i, sticky='nsew')
            d['tooltip'] = Hovertip_CustomFont(d['checkbox'], f'{f}', self.monofont, hover_delay=50)
            self.frequency_data[f] = d
            self.freqsel_frame.columnconfigure(i, weight=1)

        self.freqsel_frame.grid(row=rowidx, column=0, sticky=tk.E+tk.W)
        self.param_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1

        # Create Treamtent Pressure Input
        if power_mode in power_settings:
            self.power_mode = power_mode
        else:
            self.power_mode = [0]
        self.power_settings = power_settings
        self.power_mode_dict = {self.power_settings[mode]['label']: mode for mode in power_modes}
        power_mode_strs = list(self.power_mode_dict.keys())
        power_settings = self.power_settings[self.power_mode]
        self.power_frame = tk.Frame(self.param_frame, relief=tk.RAISED, pady=5, padx=5, borderwidth=2)

        self.power_mode_str = tk.StringVar(value=power_settings['label'])
        self.power_mode_select = tk.OptionMenu(self.power_frame,
                                               self.power_mode_str,
                                               *power_mode_strs,
                                               command=self.set_power_mode)
        self.power_mode_select.configure(width=24, anchor='w', pady=5, font=self.mediumfont)
        self.power_mode_select.grid(row=0, column=0, columnspan=2, sticky=tk.W + tk.E + tk.S)
        self.power_frame.grid_rowconfigure(0, weight=1)

        self.power_vals_dict = {mode: self.power_settings[mode]['default'] for mode in power_modes}
        self.power_value = tk.DoubleVar(value=power_settings['default'])
        self.power_slider = tk.Scale(self.power_frame,
                                     from_=power_settings['minmax'][0],
                                     to=power_settings['minmax'][1],
                                     variable=self.power_value,
                                     showvalue=True,
                                     resolution=power_settings['step'],
                                     orient=tk.HORIZONTAL,
                                     width=30,
                                     length=300,
                                     font=self.bigfont)
        self.power_slider.bind('<ButtonRelease-1>', self.set_power_value)
        self.power_slider.grid(row=1, column=0, sticky=tk.E + tk.W)
        self.power_frame.grid_rowconfigure(0, weight=1)
        self.power_frame.grid_columnconfigure(0, weight=100)
        self.power_units_label = tk.Label(self.power_frame, text=power_settings['units'], anchor='nw', width=7,
                                          height=1, font=self.bigfont)
        self.power_units_label.grid(row=1, column=1, sticky=tk.W + tk.S)
        self.power_frame.grid_columnconfigure(1, weight=1)
        self.power_frame.grid(row=rowidx, column=0, sticky=tk.E + tk.W)
        self.param_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1

        # Create Burst Length Input
        self.burst_length_frame = tk.Frame(self.param_frame)
        self.burst_lengths = burst_lengths
        if burst_length not in burst_lengths:
            burst_length = burst_lengths[0]
        self.burst_length_descs = tuple(f'{int(burst_length * 1000):0d} ms' for burst_length in self.burst_lengths)
        self.burst_length_str = tk.StringVar(value=self.burst_length_descs[self.burst_lengths.index(burst_length)])
        self.burst_length_label = tk.Label(self.burst_length_frame, text='Burst Length:', anchor='nw',
                                           font=self.mediumfont, width=12)
        self.burst_length_menu = tk.OptionMenu(self.burst_length_frame,
                                               self.burst_length_str,
                                               *self.burst_length_descs,
                                               command=self.set_burst_length)
        self.burst_length_menu.configure(width=6, font=self.mediumfont, anchor='w')
        self.duty_cycle_label = tk.Label(self.burst_length_frame, text='Duty Cycle:', anchor='nw',
                                         font=self.mediumfont, width=12)
        duty_cycle_strs = [f'{duty_cycle * 100:0.3g}%' for duty_cycle in duty_cycles]
        self.duty_cycle_dict = {duty_cycle_str: val for duty_cycle_str, val in
                                zip(duty_cycle_strs, duty_cycles)}
        duty_cycle_index = duty_cycles.index(duty_cycle)
        self.duty_cycle_str = tk.StringVar(value=duty_cycle_strs[duty_cycle_index])
        self.duty_cycle_menu = tk.OptionMenu(self.burst_length_frame,
                                             self.duty_cycle_str,
                                             *duty_cycle_strs,
                                             command=self.set_duty_cycle)
        self.duty_cycle_menu.configure(width=6, font=self.mediumfont, anchor='w')
        self.burst_length_label.grid(row=0, column=0, sticky=tk.W)
        self.burst_length_menu.grid(row=0, column=1, sticky=tk.E)
        self.duty_cycle_label.grid(row=0, column=2, sticky=tk.W)
        self.duty_cycle_menu.grid(row=0, column=3, sticky=tk.E)

        # Create Treatment Duration Input
        self.duration_label = tk.Label(self.burst_length_frame, text='Treatment Duration:', anchor='nw',
                                       font=self.mediumfont, width=20)
        self.duration_val = tk.IntVar(value=0)
        self.durations = durations
        if duration not in self.durations:
            duration = self.durations[0]
        self.duration_descriptions = tuple((config_time(t) for t in durations))
        self.duration_str = tk.StringVar(value=self.duration_descriptions[self.durations.index(duration)])
        self.duration_menu = tk.OptionMenu(self.burst_length_frame, self.duration_str, *self.duration_descriptions,
                                           command=self.set_duration)
        self.duration_menu.configure(width=6, font=self.mediumfont, anchor='w')
        self.duration_label.grid(row=1, column=2, sticky=tk.W)
        self.duration_menu.grid(row=1, column=3, sticky=tk.E)
        for i in (0, 2):
            self.burst_length_frame.grid_columnconfigure(i, weight=2, pad=10)
        for i in (1, 3):
            self.burst_length_frame.grid_columnconfigure(i, weight=1, pad=10)
        self.burst_length_frame.grid_rowconfigure("all", weight=1)

        self.burst_length_frame.grid(row=rowidx, column=0, sticky=tk.E+tk.W)
        self.param_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1
        self.param_frame.grid_columnconfigure(0, weight=1)
        self.param_frame.grid(row=frowidx, column=0, sticky=tk.E+tk.W)
        self.grid_rowconfigure(frowidx, weight=4)
        frowidx += 1

        # Create Treatment Controls Frame
        self.treat_frame = tk.Frame(self, padx=10, pady=10)
        rowidx = 0
        self.startpause_button = tk.Button(self.treat_frame, text='Start', command=self.start_pause, state=tk.DISABLED,
                                           font=self.bigfont, width=30)
        if simulate:
            self.startpause_button.configure(text='Start Simulation')
        self.startpause_button.grid(row=rowidx, column=0, sticky=tk.E+tk.W)
        self.abort_button = tk.Button(self.treat_frame, text='Abort', command=self.abort, state=tk.DISABLED,
                                      font=self.bigfont, width=30)
        self.abort_button.grid(row=rowidx, column=1, sticky=tk.E+tk.W)
        self.treat_frame.grid_rowconfigure(rowidx, weight=1)
        self.treat_frame.grid_columnconfigure(0, weight=1)
        self.treat_frame.grid_columnconfigure(1, weight=1)

        self.barstyle = ttk.Style()
        self.barstyle.theme_use('default')
        self.barstyle.configure("my.Horizontal.TProgressbar", foreground='red', background='red')
        rowidx += 1
        self.pbar_label_var = tk.StringVar(value='')
        self.pbar_label = tk.Label(self.treat_frame, textvariable=self.pbar_label_var, anchor='nw', font=self.bigfont)
        self.pbar_label.grid(row=rowidx, column=0, columnspan=2, sticky=tk.E+tk.W)
        self.treat_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1
        self.pbar = ttk.Progressbar(self.treat_frame, orient='horizontal', mode='determinate', length=200, style="my.Horizontal.TProgressbar")
        self.pbar.grid(row=rowidx, column=0, columnspan=2, sticky=tk.E+tk.W)
        self.treat_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1
        self.tbar_label_var = tk.StringVar(value='')
        self.tbar_label = tk.Label(self.treat_frame, textvariable=self.tbar_label_var, anchor='nw', font=self.bigfont)
        self.tbar_label.grid(row=rowidx, column=0, columnspan=2, sticky=tk.E+tk.W)
        self.treat_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1
        self.tbar = ttk.Progressbar(self.treat_frame, orient='horizontal', mode='determinate', length=200, style="my.Horizontal.TProgressbar")
        self.tbar.grid(row=rowidx, column=0, columnspan=2, sticky=tk.E+tk.W)
        self.treat_frame.grid_rowconfigure(rowidx, weight=1)
        rowidx += 1
        self.treat_frame.grid(row=frowidx, column=0, sticky=tk.E+tk.W)
        self.grid_rowconfigure(frowidx, weight=2)
        frowidx += 1
        self.grid_columnconfigure(0, weight=1)

        # Pack all elements
        self.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.voltage_calibration = voltage_calibration
        self.amplifier_gain = amplifier_gain
        self.controller = controller.Controller(frequencies=[],
                                                pressure=self.power_vals_dict[self.power_mode],
                                                burst_duty_cycle=duty_cycle,
                                                duration=duration,
                                                simulate=simulate)
        self.update_pressure_strings()
        self.control_queue = controller.ControlQueue(self.controller, on_open=self.on_open, on_treat=self.on_treat,
                                                     on_wait=self.on_wait, on_end=self.on_end, on_error=self.on_error)
        self.is_running = False
        self.is_started = False
        config.REBOOT = False
        logger.info('[init] App started')

    def load_config(self, config_name):
        """
        Load a configuration

        :param config_name: Name of the configuration to load
        """
        config_id = config.CONFIG_IDS[config.CONFIG_NAMES.index(config_name)]
        prev_id = config.get_config_id()
        if not config_id == prev_id:
            logger.info(f'[load_config] Rebooting into configuration {config_id}')
            config.set_config_id(config_id)
            config.REBOOT = True
            self.quit_app()

    def set_simulate(self):
        """
        Set simulation mode. 
        If simulation mode is enabled, the controller will not be connected

        :return: None
        """
        simulate = self.simulate_var.get() == 1
        logger.info(f'[set_simulate] Set controll.simulation to {simulate}')
        self.controller.simulate = simulate
        if simulate:
            self.top.title(f'OpenWater Oncolysis Controller (SIMULATE MODE)')
        else:
            self.top.title(f'OpenWater Oncolysis Controller')

    def toggle_connect(self):
        """
        Toggle connection to the controller
        """
        if self.controller.is_connected:
            logger.info('[disconnect] Disconnecting...')
            self.control_queue.kill()
            self.toggle_connect_button.configure(text='Connect')
            self.check_ready()
            if len(self.config_names) > 1:
                self.config_select.configure(state='normal')
            self.simulate_checkbox.configure(state='normal')
        else:
            logger.info('[connect] Connecting...')
            self.set_controls_enabled(False)
            self.config_select.configure(state='disabled')
            self.simulate_checkbox.configure(state='disabled')
            self.toggle_connect_button.configure(text='Connecting...', state=tk.DISABLED)
            self.root.update()
            self.control_queue.start_queue()
            self.control_queue.open()

    def set_controls_enabled(self, enabled):
        """
        Enable or disable all controls

        :param enabled: True to enable, False to disable
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        all_controls = [cb['checkbox'] for cb in self.frequency_data.values()] + \
                       [self.power_slider,
                        self.duration_menu,
                        self.toggle_connect_button,
                        self.burst_length_menu,
                        self.duty_cycle_menu,
                        self.power_mode_select]
        for control in all_controls:
            control.configure(state=state)

    def set_frequencies(self, freq):
        """
        Set the frequencies to be used for treatment

        :param freq: list of frequencies to use
        """
        status_str = ('Removing', 'Adding')
        status = self.frequency_data[freq]['var'].get()
        logger.info(f'[set_frequencies] {status_str[status]} {freq} kHz')
        selected_frequencies = self.get_frequencies()
        self.controller.set_frequencies(selected_frequencies)
        self.check_ready()
        self.update_pressure_strings()

    def set_power_mode(self, power_mode_str):
        """
        Switch between pressure modes

        :param: power_mode_str string from dropdown
        """
        logger.info(f'[set_pressure_mode] Setting pressure mode to {power_mode_str}')
        # look up mode based on selection
        self.power_mode = self.power_mode_dict[power_mode_str]
        power_settings = self.power_settings[self.power_mode]
        # configure the slider
        self.power_slider.configure(from_=power_settings['minmax'][0],
                                    to=power_settings['minmax'][1],
                                    resolution=power_settings['step'])
        # set the slider to the new value and update the controller
        self.power_value.set(self.power_vals_dict[self.power_mode])
        self.power_units_label.configure(text=power_settings['units'])
        self.controller.power_mode = self.power_mode
        self.set_power_value()

    def set_power_value(self, event=None):
        """
        Update the controller's pressure setting

        :param: event (optional) event that triggered the update
        """
        if not self.is_started:
            power_value = self.power_value.get()
            power_settings = self.power_settings[self.power_mode]
            units = power_settings["units"]
            logger.info(f'[set_pressure] Setting power ({power_settings["label"]}) to {power_value} {units}')
            self.power_vals_dict[self.power_mode] = power_value
            self.controller.power_value = power_value
            self.update_pressure_strings()

    def update_pressure_strings(self):
        """
        Update the pressure strings for each frequency
        """
        warn_logo = '[!]'
        ok_logo = ''
        for f in self.frequencies:
            pressure_target = self.controller.calc_pressure_target(f, self.power_vals_dict[self.power_mode])
            voltage_target = self.controller.calc_voltage(f, pressure_target)
            MI = pressure_target*1e-3/np.sqrt(f*1e-3)
            warn_mi = warn_logo if MI > 1.91 else ok_logo
            isppa = (pressure_target*1e3)**2/3e6/1e4
            warn_isppa = warn_logo if isppa > 190.1 else ok_logo
            warn_v = warn_logo if voltage_target > 1.01 else ok_logo
            adjusted_burst_length = self.controller.calc_burst_length(f)
            period = self.controller.burst_length / self.controller.burst_duty_cycle
            adjusted_duty_cycle = adjusted_burst_length/period
            ispta = isppa*adjusted_duty_cycle*1e3
            warn_ispta = warn_logo if ispta > 720.1 else ok_logo
            label_text = f'{f} kHz\n' \
                         f'{"MI":<6}:{MI:5.2f} {"":6} {warn_mi}\n' \
                         f'{"PNP":<6}:{pressure_target:5.0f} {"kPa":6}\n' \
                         f'{"Vin":<6}:{1e3 * voltage_target:5.0f} {"mV":6} {warn_v}\n' \
                         f'{"ISPPA":<6}:{isppa:5.1f} {"W/cm2":6} {warn_isppa}\n' \
                         f'{"ISPTA":<6}:{ispta:5.0f} {"mW/cm2":6} {warn_ispta}\n' \
                         f'{"BURST":<6}:{adjusted_burst_length*1e3:5.3g} {"ms":6}\n' \
                         f'{"PERIOD":<6}:{period*1e3:5.3g} {"ms":6}\n' \
                         f'{"DUTY":<6}:{adjusted_duty_cycle*100:5.3g} {"%":6}'
            self.frequency_data[f]['tooltip'].text = label_text
            if any((warn_mi, warn_isppa, warn_ispta, warn_v)):
                self.frequency_data[f]['checkbox'].configure(foreground='#903000')
            else:
                self.frequency_data[f]['checkbox'].configure(foreground='#002030')

    def set_burst_length(self, burst_length_desc):
        """
        Update the controller's burst length setting

        :param: burst_length_desc string from dropdown
        """
        burst_length_index = self.burst_length_descs.index(burst_length_desc)
        burst_length = self.burst_lengths[burst_length_index]
        logger.info(f'[set_burst_length] Setting burst length to {burst_length_desc}')
        self.controller.set_burst_length(burst_length)
        self.update_pressure_strings()

    def set_duty_cycle(self, duty_cycle_str):
        """
        Update the controller's duty cycle setting

        :param: duty_cycle_str string from dropdown
        """
        duty_cycle = self.duty_cycle_dict[duty_cycle_str]
        logger.info(f'[set_duty_cycle] Setting duty cycle to {duty_cycle_str}')
        self.controller.set_duty_cycle(duty_cycle)
        self.update_pressure_strings()

    def set_duration(self, duration):
        """
        Update the total treatment duration (for each frequency)

        :param: duration string from dropdown
        """
        duration_index = self.duration_descriptions.index(duration)
        logger.info(f'[set_duration] Setting treatment duration to [{duration_index}] {duration}')
        self.controller.duration = self.durations[duration_index]

    def get_frequencies(self):
        """
        Get the list of frequencies to treat

        :return: list of frequencies to treat
        """
        return [freq for freq in self.frequencies if self.frequency_data[freq]['var'].get()]

    def get_power(self):
        """
        Get the power setting

        :return: power value
        """
        return self.power_value.get()

    def get_duration(self):
        """
        Get the treatment duration

        :return: (treatment duration in seconds, index, duration string)
        """
        duration_str = self.duration_str.get()
        duration_index = self.duration_descriptions.index(duration_str)
        duration = self.durations[duration_index]
        return duration, duration_index, duration_str

    def check_ready(self):
        """
        Check if the controller is ready to start a treatment
        """
        ready = self.controller.is_ready()
        ready_state = tk.NORMAL if ready else tk.DISABLED
        self.startpause_button.configure(state=ready_state)

    def on_open(self):
        """
        Callback function for when the controller is connected
        """
        if self.controller.connection_error:
            self.toggle_connect_button.configure(state=tk.NORMAL, text='Failed to Connect. Click to Reset.')
        else:
            self.toggle_connect_button.configure(state=tk.NORMAL, text='Disconnect')
        if self.controller.simulate:
            self.top.title(f'OpenWater Oncolysis Controller (SIMULATE MODE)')
            self.startpause_button.configure(text='Start Simulation')
            self.simulate_var.set(1)
        else:
            self.top.title(f'OpenWater Oncolysis Controller')
            self.startpause_button.configure(text='Start')
        self.set_controls_enabled(True)
        self.check_ready()

    def on_treat(self, index):
        """
        Callback function for when a treatment is started

        :param index: index of the frequency being treated
        """
        logger.info(f'[on_treat] treatment {index}')
        freqs = self.get_frequencies()
        n = len(freqs)
        self.pbar['value'] = 100 * (index + 1) / n
        self.pbar_label_var.set(f'[{index + 1}/{n}] {freqs[index]} kHz')
        self.root.update_idletasks()

    def on_wait(self, elapsed_time, max_time):
        """
        Callback function for when the controller is waiting

        :param elapsed_time: time elapsed since the start of the treatment
        :param max_time: maximum time to wait
        """
        tstr = config_time(elapsed_time)
        tmaxstr = config_time(max_time)
        self.tbar_label_var.set(f'{tstr} / {tmaxstr}')
        self.tbar['value'] = 100 * min(1, elapsed_time / max_time)
        self.root.update_idletasks()

    def on_end(self, message='Treatment Complete'):
        """
        Callback function for when a treatment is finished

        :param message: message to display. Default is 'Treatment Complete'
        """
        logger.info(f'[on_end] {message}')
        self.is_running = False
        self.is_started = False
        self.abort_button.configure(state=tk.DISABLED)
        self.root.update_idletasks()
        if self.controller.simulate:
            self.startpause_button.configure(text='Start Simulation')
        else:
            self.startpause_button.configure(text='Start')
        #self.pbar['value'] = 0
        #self.tbar['value'] = 0
        self.pbar_label_var.set(message)
        #self.tbar_label_var.set('')
        self.set_controls_enabled(True)
        self.check_ready()

    def on_error(self, err):
        """
        Callback function for when an error occurs

        :param err: error message
        """
        logger.critical(f"[controller.on_error] Unexpected {err=}, {type(err)=}")
        logger.critical(f"[controller.on_error] {traceback.format_exc()}")
        messagebox.showerror(title='ERROR!', message=str(err))
        self.barstyle.configure("my.Horizontal.TProgressbar", foreground='red', background='red')
        self.pbar_label_var.set('Error. Restart required.')
        self.controller.connection_error = True
        self.toggle_connect_button.configure(state=tk.DISABLED)
        self.set_controls_enabled(False)
        self.check_ready()

    def start_pause(self):
        """
        Callback to start or pause the treatment
        """
        if not self.is_running:
            self.start_treatment()
        else:
            self.pause_treatment()

    def start_treatment(self):
        """
        Start or resume the treatment
        """
        if not self.is_started:
            freqs = self.get_frequencies()
            power_val = self.get_power()
            power_settings = self.power_settings[self.power_mode]
            duration, duration_idx, duration_str = self.get_duration()
            logger.info(f'[start_treatment] Treatment Parameters:')
            logger.info(f'[start_treatment] Frequencies: {freqs}')
            logger.info(f'[start_treatment] Power Mode: {power_settings["label"]}')
            logger.info(f'[start_treatment] Power: {power_val} {power_settings["units"]}')
            logger.info(f'[start_treatment] Duration: {duration} (option {duration_idx})')
            self.set_controls_enabled(False)
            logger.info(f'[start_treatment] Starting Treatment')
            self.is_started = True
            self.control_queue.start()
        else:
            logger.info(f'[start_treatment] Resuming Treatment')
            self.control_queue.resume()
        self.barstyle.configure("my.Horizontal.TProgressbar", foreground='green', background='green')
        self.startpause_button.configure(text='Pause')
        self.abort_button.configure(state=tk.NORMAL)
        self.is_running = True

    def pause_treatment(self):
        """
        Pause the treatment
        """
        logger.info(f'[pause_treatment] Pause')
        self.control_queue.pause()
        self.startpause_button.configure(text='Resume')
        self.barstyle.configure("my.Horizontal.TProgressbar", foreground='yellow', background='yellow')
        self.is_running = False

    def abort(self):
        """
        Abort the treatment
        """
        logger.info(f'[pause_treatment] Abort')
        self.control_queue.stop()
        self.control_queue.reset()
        self.barstyle.configure("my.Horizontal.TProgressbar", foreground='red', background='red')
        self.on_end(message='Treatment Aborted')

    def quit_app(self):
        """
        Quit the application
        """
        try:
            if self.controller.is_connected:
                self.control_queue.kill()
        finally:
            logger.info('[quit_app] Exiting...')
            self.root.destroy()
            if not config.REBOOT:
                raise SystemExit


def runapp(simulate=False, config_ids=config.CONFIG_IDS):
    """
    Launch GUI

    :param simulate: If True, the application will run in simulation mode, which will not communicate with the hardware
    :param config_ids: A list of configuration IDs
    :return: None
    """
    root = tk.Tk()
    root.iconbitmap(os.path.join(HERE, 'app.ico'))
    root.geometry("720x650+0+0")
    myapp = App(root, simulate=simulate, config_ids=config_ids)

    def on_closing():
        myapp.quit_app()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    myapp.mainloop()



class Hovertip_CustomFont(tooltip.Hovertip):
    """Create a text tooltip with a mouse hover delay.

    anchor_widget: the widget next to which the tooltip will be shown
    hover_delay: time to delay before showing the tooltip, in milliseconds

    Note that a widget will only be shown when showtip() is called,
    e.g. after hovering over the anchor widget with the mouse for enough
    time.
    """
    def __init__(self, anchor_widget, text, custom_font, hover_delay=1000):
        super().__init__(anchor_widget, text, hover_delay=hover_delay)
        self.text = text
        self.font = custom_font

    def showcontents(self):
        label = tk.Label(self.tipwindow, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=self.font)
        label.pack()