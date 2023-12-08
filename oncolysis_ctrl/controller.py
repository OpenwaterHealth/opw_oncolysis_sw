import queue
import tkinter.messagebox
from multiprocessing import Queue
from threading import Thread
from oncolysis_ctrl import config, rf_switch, function_generator
import logging
import time
import numpy as np
import traceback
logger = logging.getLogger("oc.controller")
constants = config.constants
PRESSURE = constants.POWER_SETTINGS[constants.POWER_MODE]['default']


class Controller(object):
    """ 
    Controller class for the Oncolysis System    
    """
    def __init__(self, frequencies=constants.FREQUENCIES_KHZ, pressure=PRESSURE,
                 duration=constants.DURATION_S, transmit_channel=constants.TRANSMIT_CHANNEL,
                 rf_switch_settings=constants.RF_SWITCH_SETTINGS, rf_switch_sn=constants.RADIALL_SN,
                 burst_params=constants.BURST_PARAMS_TEMPLATE, burst_length=constants.BURST_LENGTH,
                 power_mode=constants.POWER_MODE,
                 source_params_template=constants.SOURCE_PARAMS_TEMPLATE,
                 burst_params_template=constants.BURST_PARAMS_TEMPLATE,
                 burst_duty_cycle=constants.BURST_DUTY_CYCLE, amplifier_gain=constants.AMPLIFIER_GAIN,
                 voltage_calibration=constants.CALIB, simulate=False):
        """
        Controller constructor
        :param frequencies: list of frequencies to treat
        :param pressure: pressure to treat at
        :param duration: duration of treatment
        :param transmit_channel: channel to transmit on
        :param rf_switch_settings: settings for the RF Switch
        :param rf_switch_sn: serial number of the RF Switch
        :param burst_params: burst parameters
        :param burst_length: burst length
        :param power_mode: power mode
        :param source_params_template: source parameters
        :param burst_params_template: burst parameters
        :param burst_duty_cycle: burst duty cycle
        :param amplifier_gain: amplifier gain
        :param voltage_calibration: voltage calibration
        :param simulate: simulate hardware
        """
        self.fgen = function_generator.FunctionGenerator()
        self.xmit = self.fgen.channels[transmit_channel]
        self.switches = tuple(rf_switch.RFSwitch(sn=sn) for sn in rf_switch_sn)
        self.rf_switch_settings = rf_switch_settings
        self.frequencies = frequencies
        self.power_value = pressure
        self.burst_params = burst_params
        self.burst_length = burst_length
        self.duration = duration
        self.is_connected = False
        self.connection_error = False
        self.simulate = simulate
        self.frequency = None
        self.treat_time_start = None
        self.treat_time_elapsed = 0
        self.treat_on = False
        self.power_mode = power_mode
        self.voltage = 0
        self.source_params_template = source_params_template
        self.burst_params_template = burst_params_template
        self.burst_duty_cycle = burst_duty_cycle
        self.amplifier_gain = amplifier_gain
        self.voltage_calibration = voltage_calibration
        self.update_voltage()

    def open(self):
        """
        Open Connection to Hardware
        :return: None
        """
        if self.is_connected:
            logger.error('[disconnect] Already Connected')
        else:
            self.connection_error = False
            if not self.simulate:
                try:
                    self.fgen.open()
                    self.xmit.set_output(enabled=False)
                    self.xmit.apply(**self.source_params_template)
                    self.xmit.set_burst(**self.burst_params_template)
                    for switch in self.switches:
                        switch.open()
                    logger.info('[open] Connected')
                except ConnectionError as e:
                    msgbox = tkinter.messagebox.askquestion('Could not connect to hardware',
                                                            'Open in simulation mode?',
                                                            icon='warning')
                    if msgbox == 'yes':
                        logger.warning('[open] Could not connect to hardware. Opening in simulation mode')
                        self.simulate = True
                    else:
                        logger.error('[open] Could not connect to hardware.')
                        self.connection_error = True
            self.is_connected = True

    def close(self):
        """
        Close Connection to Hardware
        :return: None
        """
        if not self.is_connected:
            logger.error('[close] Already Disconnected')
        else:
            if not self.simulate:
                self.fgen.close()
                for switch in self.switches:
                    switch.close()
            self.is_connected = False
            logger.info('[close] Disconnected')

    def is_ready(self):
        """
        Check if device is ready to treat
        :return: True if ready, False otherwise
        """
        return self.is_connected and (len(self.frequencies) > 0) and not self.connection_error

    def set_frequencies(self, frequencies):
        """
        Set frequencies to treat
        :param frequencies: list of frequencies to treat
        :return: None
        """
        self.frequencies = frequencies
        logger.info(f'[set_frequencies] Set frequencies to {frequencies}')

    def set_frequency(self, frequency_khz):
        """
        Set frequency to treat
        :param frequency_khz: frequency to treat
        :return: None
        """
        if not self.is_ready():
            logger.error(f'[set_frequency] device not ready')
            raise ConnectionError('device not ready')
        self.frequency = frequency_khz
        self.update_voltage()
        burst_length = self.calc_burst_length(frequency_khz)
        burst_cycles = int(burst_length * 1e3 * frequency_khz)
        burst_period = self.burst_params['period']
        logger.info(f'[set_frequency] Set frequency to {frequency_khz} kHz')
        logger.info(f'[set_frequency] set voltage to {self.voltage:0.3f} V')
        logger.info(f'[set_frequency] set burst to {burst_cycles} cycles ({burst_length*1e3:0.3g} ms),'
                    f'period={burst_period*1e3:0.4g} ms')
        if not self.simulate:
            if frequency_khz in self.rf_switch_settings:
                for switch, position in zip(self.switches, self.rf_switch_settings[frequency_khz]):
                    switch.set_position(position)
            else:
                logger.warning(f"[set_frequency] Unmapped frequency {frequency_khz}. Can't set RF Switch")
            self.xmit.set_frequency(frequency=frequency_khz * 1e3)
            self.xmit.set_voltage(voltage=self.voltage)
            self.xmit.set_burst(cycles=burst_cycles,
                                period=burst_period)
            settings = self.xmit.get_settings()
            logger.info('[set_frequency] Verify source settings:')
            for key, val in settings.items():
                logger.info(f'[set_frequency]     {key} = {val}')
            burst = self.xmit.get_burst()
            logger.info('[set_frequency] Verify burst settings:')
            for key, val in burst.items():
                logger.info(f'[set_frequency]     {key} = {val}')

    def set_pressure(self, pressure):
        """
        Set pressure to treat at
        :param pressure: pressure to treat at
        :return: None
        """
        if not self.is_ready():
            logger.error(f'[set_pressure] device not ready')
            raise ConnectionError('device not ready')
        self.power_value = pressure

        logger.info(f'[set_pressure] Pressure={pressure}, Voltage={self.voltage}')
        if not self.simulate:
            self.xmit.set_voltage(voltage=self.voltage)

    def update_voltage(self):
        """
        Update voltage based on frequency and power settings
        :return: None
        """
        pressure_target = self.calc_pressure_target(self.frequency, self.power_value)
        logger.info(f'[update_voltage] target pressure: {pressure_target} kPa')
        target_voltage = self.calc_voltage(self.frequency, pressure_target)
        amplified_voltage = target_voltage * self.amplifier_gain
        logger.info(f'[update_voltage] output voltage:{amplified_voltage: 0.1f} V, input_voltage:{target_voltage: 0.3f} V')
        self.voltage = target_voltage

    def calc_voltage(self, frequency, pressure_target):
        """
        Calculate voltage based on frequency and pressure settings
        :param frequency: frequency to treat at
        :param pressure_target: pressure to treat at
        :return: voltage
        """
        if frequency is None:
            return 0
        a = self.voltage_calibration[frequency]['coeff_a']
        b = self.voltage_calibration[frequency]['coeff_b']
        c = -1 * pressure_target
        amplified_voltage = np.round((-b + np.sqrt(b ** 2 - 4 * a * c)) / (2 * a), 2)
        target_voltage = amplified_voltage / self.amplifier_gain
        return target_voltage

    def calc_pressure_target(self, frequency, value):
        """
        Calculate pressure based on frequency and power settings
        :param frequency: frequency to treat at
        :param value: power setting
        :return: pressure
        """
        if frequency is None:
            return 0
        if self.power_mode == 'constant_mi':
            pressure_target = value / 100 * self.voltage_calibration[frequency]['p_ref']
        elif self.power_mode == 'constant_pressure':
            pressure_target = value
        elif self.power_mode == 'constant_ispta':
            isppa = value*1e-3 / self.burst_duty_cycle # W/cm2
            pressure_target = np.sqrt(isppa*3e6)*1e-1
        elif self.power_mode == 'constant_ispta_mi100':
            pressure_target = self.voltage_calibration[frequency]['p_ref']
        elif  self.power_mode == 'constant_isppa':
            isppa = value
            pressure_target = np.sqrt(isppa*3e6)*1e-1
        else:
            raise ValueError(f'Bad power mode {self.power_mode}')
        return pressure_target

    def calc_burst_length(self, frequency):
        """
        Calculate burst length based on frequency and power settings
        :param frequency: frequency to treat at
        :return: burst length
        """
        if frequency is None:
            return self.burst_length
        if self.power_mode == 'constant_ispta_mi100':
            pressure_kpa = self.voltage_calibration[frequency]['p_ref']  # Pressure @ MI1.9
            isppa = (pressure_kpa*1e3)**2 / 3e6/1e4
            ispta = self.power_value
            max_burst_length = self.burst_length
            period = max_burst_length/self.burst_duty_cycle
            adjusted_duty_cycle = ispta*1e-3/isppa
            adjusted_burst_length = period*adjusted_duty_cycle
        else:
            adjusted_burst_length = self.burst_length
        return adjusted_burst_length

    def set_burst_length(self, burst_length):
        """
        Set burst length
        :param burst_length: burst length
        :return: None
        """
        self.burst_params['period'] = burst_length * np.round(1 / self.burst_duty_cycle, 4)
        self.burst_length = burst_length
        logger.info(f'[set_burst_length] Burst length = {self.burst_length}, Period = {self.burst_params["period"]}')

    def set_duty_cycle(self, duty_cycle):
        """
        Set duty cycle
        :param duty_cycle: duty cycle
        :return: None
        """
        self.burst_duty_cycle = duty_cycle
        self.burst_params['period'] = self.burst_length * np.round(1 / self.burst_duty_cycle, 4)
        logger.info(f'[set_duty_cycle] Burst length = {self.burst_length}, Period = {self.burst_params["period"]}')

    def set_duration(self, duration):
        """
        Set duration
        :param duration: duration
        :return: None
        """
        self.duration = duration
        logger.info(f'[set_duration] Set duration to {duration}')

    def start_treatment(self, reset_timer=True):
        """
        Start treatment
        :param reset_timer: reset timer. Default True
        :return: None
        """
        if self.is_ready():
            if self.treat_on:
                logger.warning('[start_treatment] Already on')
            else:
                logger.info(f'[start_treatment] Treating {self.frequency} kHz')
                if reset_timer or (self.treat_time_start is None):
                    self.treat_time_elapsed = 0
                self.treat_time_start = time.time()
                self.treat_on = True
                if not self.simulate:
                    self.xmit.set_output(enabled=True)
        else:
            logger.error(f'[start_treatment] device not ready')
            raise ConnectionError('[start_treatment] device not ready')

    def check_treatment_time(self):
        """
        Check treatment time since start
        :return: treatment time
        """
        if not self.treat_on:
            time_elapsed = self.treat_time_elapsed
        else:
            segment_time = time.time() - self.treat_time_start
            time_elapsed = self.treat_time_elapsed + segment_time
        return time_elapsed

    def stop_treatment(self, reset_timer=True, wait_for_time=0):
        """
        Stop treatment
        :param reset_timer: reset timer. Default True
        :param wait_for_time: wait for time. Default 0
        :return: None
        """
        if not self.treat_on:
            logger.warning('[stop_treatment] Treatment is not active')
        else:
            total_time_elapsed = self.check_treatment_time()
            if wait_for_time > total_time_elapsed:
                logger.info(f'[stop_treatment] Waiting for treatment time to reach {wait_for_time:0.2f} s')
                time.sleep(wait_for_time-total_time_elapsed)
            if not self.simulate:
                self.xmit.set_output(enabled=False)
            self.treat_on = False
            logger.info(f'[stop_treatment] Stopped treatment (elapsed time: {total_time_elapsed:0.2f})')
            if reset_timer:
                logger.info(f'[stop_treatment] Resetting timer')
                self.treat_time_elapsed = 0
                self.treat_time_start = None
            else:
                self.treat_time_elapsed = total_time_elapsed


class ControlQueue:
    """
    Control Queue for Oncolysis System
    """
    def __init__(self, controller, on_open=None, on_treat=None, on_wait=None, on_end=None, on_close=None, on_error=None):
        """
        Control Queue constructor
        :param controller: controller object
        :param on_open: callback to execute on open
        :param on_treat: callback to execute on treat
        :param on_wait: callback to execute on wait
        :param on_end: callback to execute on end
        :param on_close: callback to execute on close
        :param on_error: callback to execute on error
        :return: None
        """
        self.controller = controller
        self.control_queue = Queue()
        self.on_open = on_open
        self.on_treat = on_treat
        self.on_wait = on_wait
        self.on_end = on_end
        self.on_close = on_close
        self.on_error = on_error
        self.control_loop_thread = self.get_new_thread()

    def get_new_thread(self):
        """
        Create a new thread
        :return: [Thread] new thread
        """
        return Thread(target=control_loop, args=(self.controller, self.control_queue, self.on_open, self.on_treat,
                                                 self.on_wait, self.on_end, self.on_close, self.on_error))

    def start_queue(self):
        """
        Start the queue thread
        :return: None
        """
        self.control_loop_thread.start()

    def put(self, msg):
        """
        Put a message in the queue
        :param msg: message to put in the queue
        :return: None
        """
        if self.control_loop_thread.is_alive():
            self.control_queue.put(msg)
        else:
            raise ConnectionError('Thread not Running')

    def open(self):
        """
        Submit a command to open the connection to the hardware
        """
        self.put('OPEN')

    def start(self):
        """
        Submit a command to start the treatment
        """
        self.put('START')

    def resume(self):
        """
        Submit a command to resume the treatment
        """
        self.put('RESUME')

    def pause(self):
        """
        Submit a command to pause the treatment
        """
        self.put('PAUSE')

    def stop(self):
        """
        Submit a command to stop the treatment
        """
        self.put('STOP')

    def reset(self):
        """
        Submit a command to reset
        """
        self.put('RESET')

    def treat(self):
        """
        Submit a command to treat
        """
        self.put('TREAT')

    def kill(self):
        """
        Submit a command to kill the thread
        """
        self.put('KILL')
        self.control_loop_thread.join()
        self.control_loop_thread = self.get_new_thread()


def control_loop(controller, control_queue, on_open=None, on_treat=None, on_wait=None, on_end=None, on_close=None, on_error=None):
    """
    Control Loop for Oncolysis System
    :param controller: controller object
    :param control_queue: control queue
    :param on_open: callback to execute on open
    :param on_treat: callback to execute on treat
    :param on_wait: callback to execute on wait
    :param on_end: callback to execute on end
    :param on_close: callback to execute on close
    :param on_error: callback to execute on error
    :return: None
    """
    logger.info('[control_loop] started')

    def start_freq_index(index):
        """
        Start treating at a given frequency index
        :param index: frequency index
        :return: None
        """
        freq = controller.frequencies[index]
        controller.set_frequency(frequency_khz=freq)
        logger.info(f'[control_loop] Starting {freq} kHz')
        controller.start_treatment(reset_timer=True)
        if on_treat is not None:
            on_treat(index)

    try:
        run_flag = False
        freq_index = 0
        while True:
            try:
                command = control_queue.get(False)
            except queue.Empty:
                if run_flag:
                    treat_time = controller.check_treatment_time()
                    if on_wait is not None:
                        on_wait(treat_time, controller.duration)
                    if treat_time >= controller.duration:
                        logger.info(f'[control_loop] {controller.frequency} kHz complete')
                        controller.stop_treatment(reset_timer=True)
                        freq_index += 1
                        if freq_index < len(controller.frequencies):
                            start_freq_index(freq_index)
                        else:
                            logger.info(f'[control_loop] Sequence complete')
                            run_flag = False
                            if on_end is not None:
                                on_end()
                time.sleep(0.1)
                continue
            logger.info(f'[control_loop] {command} received')
            if command == 'OPEN':
                controller.open()
                if on_open is not None:
                    on_open()
            elif command == 'CLOSE':
                controller.close()
            elif command == 'START':
                freq_index = 0
                start_freq_index(freq_index)
                run_flag = True
            elif command == 'PAUSE':
                controller.stop_treatment(reset_timer=False)
                run_flag = True
            elif command == 'RESUME':
                controller.start_treatment(reset_timer=False)
                run_flag = True
            elif command == 'STOP':
                controller.stop_treatment(reset_timer=True)
                run_flag = False
            elif command == 'RESET':
                freq_index = 0
                run_flag = False
            elif command == 'TREAT':
                controller.start_treatment(reset_timer=True)
                controller.stop_treatment(reset_timer=True, wait_for_time=controller.duration)
            elif command == 'KILL':
                break

    except BaseException as err:
        logger.critical(f"[control_loop] Unexpected {err=}, {type(err)=}")
        if on_error is not None:
            on_error(err)
    finally:
        try:
            controller.close()
            if on_close is not None:
                on_close()
            logger.info('[control_loop] shut down')
        except BaseException as err:
            logger.critical(f"[control_loop] Could not close connection!")
            if on_error is not None:
                on_error(err)

