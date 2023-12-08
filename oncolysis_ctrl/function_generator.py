import logging
import pyvisa
from oncolysis_ctrl import config
constants = config.constants

logger = logging.getLogger("oc.function_generator")


class FunctionGenerator:
    def __init__(self, vid=constants.RIGOL_DG4162_VID,
                 pid=constants.RIGOL_DG4162_PID,
                 channels=constants.CHANNELS,
                 max_voltage=constants.MAX_VOLTAGE):
        """
        Initialize function generator. Does not open connection.
        :param vid: vendor id for USB device (defaults for RIGOL DG4162)
        :param pid: product id for USB device (defaults for RIGOL DG4162)
        :param channels: tuple of available channels (default (1,2))
        :param max_voltage: maximum allowable voltage (to protect RF Amp, default 1.0V)
        """
        self.is_open = False
        self.resource = None
        self.inst = None
        self.idn = ''
        self.vid = vid
        self.pid = pid
        self.channels = {ch: Channel(ch, self.inst, max_voltage=max_voltage) for ch in channels}

    def open(self):
        """
        Opens the connection to the function generator
        :return:
        """
        if self.is_open:
            logger.warning('[close] Already connected')
        else:
            logger.info('[open] Connecting to Function Generator...')
            rm = pyvisa.ResourceManager()
            resources = rm.list_resources()
            vidstr = f'{self.vid:04X}'
            pidstr = f'{self.pid:04X}'
            matches = [resource for resource in resources if ((vidstr in resource) and (pidstr in resource))]
            n = len(matches)
            if n != 1:
                raise ConnectionError(f'Found {n} matching instruments for vid=x{self.vid:04X}, pid=x{self.pid:04X}')
            self.resource = matches[0]
            self.inst = rm.open_resource(self.resource)
            for ch in self.channels:
                self.channels[ch].inst = self.inst
            self.idn = self.inst.query('*IDN?')
            self.is_open = True
            logger.info(f'[open] {self.idn}')

    def close(self):
        """
        Closes the connection to the function generator
        :return:
        """
        if self.is_open:
            try:
                for ch in self.channels:
                    self.channels[ch].set_output(enabled=False)
            except BaseException as e:
                logger.error('Unable to deactivate output. Attempting to reset.')
                self.inst.write('*RST')
                raise
            self.inst.close()
            self.is_open = False
            logger.info('[close] Disconnected from Function Generator')
        else:
            logger.warning('[close] Already Disconnected')


class Channel:
    def __init__(self, channel, inst, max_voltage=None):
        """
        Instantiate function generator channel
        :param channel: channel number (1 or 2 for RIGOL)
        :param inst: pyvisa connection to instrument
        :param max_voltage: maximum voltage limit (V)
        """
        self.channel = channel
        self.inst = inst
        self.max_voltage = max_voltage

    def apply(self, mode, frequency=None, amplitude=None, offset=None, phase=None, delay=None):
        """
        Apply a basic waveform to the channel. Can use short form ('SIN') or long form ('SINUSOID')
        :param mode: waveform mode ('CUSTom','HARMonic, 'NOISe', 'PULSe', 'RAMP', 'SINusoid', 'SQUare', 'USER')
        :param frequency: Hz (not available for NOISE)
        :param amplitude: V_pp, not available for NOISE, requires frequency
        :param offset: V_DC, requires frequency and amplitude
        :param phase: degrees, not available for NOISE or PULSE, requires frequency, amplitude, offset
        :param delay: seconds, only available for PULSE, requires frequency, amplitude, offset
        :return:
        """
        mode = mode.upper()
        if 'NOIS' in mode:
            arglist = [amplitude, offset]
        elif 'PULS' in mode:
            arglist = [frequency, amplitude, offset, delay]
        elif any((match in mode for match in ('CUST', 'HARM', 'RAMP', 'SIN', 'SQU', 'USER'))):
            arglist = [frequency, amplitude, offset, phase]
        else:
            raise ValueError(f'Unknown mode {mode}')

        argstr = f'SOUR{self.channel}:APPLY:{mode}'
        for i, arg in enumerate(arglist):
            if arg is not None:
                if i == 0:
                    argstr += f' {arg}'
                else:
                    argstr += f', {arg}'
            else:
                # Check for specified parameters following a None
                if any(arglist[i+1:]):
                    raise ValueError('[apply] Invalid Parameters')
                else:
                    break
        logger.info(f'[apply] {argstr}')
        self.inst.write(argstr)

    def get_settings(self):
        """
        Get basic waveform settings.
        :return: dict of settings. Usable as input with `set_input(**settings)`
        """
        settings = self.inst.query(f'SOURCE{self.channel}:APPLY?')
        logger.info(f'[get_settings] {settings}')
        setlist = settings.strip()[1:-1].split(',')
        mode = setlist[0]
        if 'NOIS' in mode:
            arglist = ['amplitude', 'offset']
        elif 'PULS' in mode:
            arglist = ['frequency', 'amplitude', 'offset', 'delay']
        elif any((match in mode for match in ('CUST', 'HARM', 'RAMP', 'SIN', 'SQU', 'USER'))):
            arglist = ['frequency', 'amplitude', 'offset', 'phase']
        else:
            raise ValueError(f'Unknown mode {mode}')
        setdict = {'mode': mode}
        for arg, val in zip(arglist, setlist[1:]):
            setdict[arg] = float(val)
        return setdict

    def set_output(self, enabled=None, impedance=None, noise_scale=None, noise_en=None,
                   polarity_invert=None, sync_invert=None, sync_en=None):
        """
        Sets the output of the particular channel
        :param bool enabled: enable the output
        :param impedance : output impedance. (ohms (int), 'INF', 'MIN', or 'MAX')
        :param noise_scale: superposed noise scale (percent, 'MIN', or 'MAX')
        :param bool noise_en : enabled superposed noise
        :param bool polarity_invert: invert the output
        :param bool sync_invert: invert the sync signal
        :param bool sync_en: enable the sync signal
        :return:
        """
        enable_map = {True: 'ON', False: 'OFF', None: None}
        inv_norm_map = {True: 'INV', False: 'NORM', None: None}
        neg_pos_map = {True: 'NEGATIVE', False: 'POSITIVE', None: None}
        d = {'STAT': enable_map[enabled],
             'IMP': impedance,
             'NOISE:SCALE': noise_scale,
             'NOISE:STATE': enable_map[noise_en],
             'POL': inv_norm_map[polarity_invert],
             'SYNC:POL': neg_pos_map[sync_invert],
             'SYNC:STATE': enable_map[sync_en]
             }
        for attr, value in d.items():
            if value is not None:
                command = f'OUTPUT{self.channel}:{attr} {value}'
                logger.info(f'[set_output] {command}')
                self.inst.write(command)

    def get_output(self):
        """
        Get the output settings for this channel
        :return: dict of output settings (usable as input with `set_output(**output)`)
        """
        enable_map = {'ON': True, 'OFF': False}
        inv_norm_map = {'NORMAL': False, 'INVERTED': True}
        neg_pos_map = {'POS': False, 'NEG': True}
        attrs = ('STAT', 'IMP', 'NOISE:SCALE', 'NOISE:STATE', 'POL', 'SYNC:POL', 'SYNC:STATE')
        d = {}
        for attr in attrs:
            command = f'OUTPUT{self.channel}:{attr}?'
            d[attr] = self.inst.query(command).strip()
        setdict = {'enabled': enable_map[d['STAT']],
                   'impedance': 'INF' if d['IMP'] == 'INFINITY' else float(d['IMP']),
                   'noise_scale': float(d['NOISE:SCALE']),
                   'noise_en': enable_map[d['NOISE:STATE']],
                   'polarity_invert': inv_norm_map[d['POL']],
                   'sync_invert': neg_pos_map[d['SYNC:POL']],
                   'sync_en': enable_map[d['SYNC:STATE']]}
        return setdict

    def set_burst(self, enabled=None, period=None, mode=None, cycles=None, phase=None, delay=None, trig_negative=None,
                  trig_source=None, trig_out_en=None, trig_out_negative=None, gate_invert=None):
        enable_map = {True: 'ON', False: 'OFF', None: None}
        inv_norm_map = {True: 'INV', False: 'NORM', None: None}
        neg_pos_map = {True: 'NEGATIVE', False: 'POSITIVE', None: None}
        if trig_out_en is None:
            trigout = None
        elif trig_out_en:
            if trig_out_negative:
                trigout = 'NEG'
            else:
                trigout = 'POS'
        else:
            trigout = 'OFF'

        d = {'STATE': enable_map[enabled],
             'INTERNAL:PERIOD': period,
             'MODE': mode,
             'NCYCLES': cycles,
             'PHASE': phase,
             'TDELAY': delay,
             'TRIG:SLOPE': neg_pos_map[trig_negative],
             'TRIG:SOURCE': trig_source,
             'TRIG:TRIGOUT': trigout,
             'GATE:POL': inv_norm_map[gate_invert]
             }
        for attr, value in d.items():
            if value is not None:
                command = f'SOURCE{self.channel}:BURST:{attr} {value}'
                logger.info(f'[set_burst] {command}')
                self.inst.write(command)

    def trig_burst(self):
        """
        Trigger a burst immediately
        :return:
        """
        logger.info(f'[trig_burst] triggering burst on channel {self.channel}')
        self.inst.write(f'SOURCE{self.channel}:BURST:TRIGGER:IMMEDIATE')

    def get_burst(self):
        """
        Get burst parameters
        :return: dict of burst mode parameters
        """
        enable_map = {'ON': True, 'OFF': False}
        inv_norm_map = {'NORM': False, 'INV': True}
        neg_pos_map = {'POS': False, 'NEG': True}
        attrs = ('STAT', 'INTERNAL:PERIOD', 'MODE', 'NCYCLES', 'PHASE', 'TDELAY', 'TRIG:SLOPE',
                 'TRIG:SOURCE', 'TRIG:TRIGOUT', 'GATE:POL')
        d = {}
        for attr in attrs:
            command = f'SOURCE{self.channel}:BURST:{attr}?'
            d[attr] = self.inst.query(command).strip()
        setdict = {'enabled': enable_map[d['STAT']],
                   'period': float(d['INTERNAL:PERIOD']),
                   'mode': d['MODE'],
                   'cycles': int(d['NCYCLES']),
                   'phase': float(d['PHASE']),
                   'delay': float(d['TDELAY']),
                   'trig_negative': neg_pos_map[d['TRIG:SLOPE']],
                   'trig_source': d['TRIG:SOURCE'],
                   'trig_out_en': not(d['TRIG:TRIGOUT'] == 'OFF'),
                   'trig_out_negative': d['TRIG:TRIGOUT'] == 'NEG',
                   'gate_invert': inv_norm_map[d['GATE:POL']]}
        return setdict

    def set_frequency(self, frequency, **kwargs):
        """
        Set frequency
        :param frequency: frequency (Hz)
        :return:
        """
        logger.info(f'[set_frequency] Setting frequency to {frequency}')
        command = f'SOURCE{self.channel}:FREQUENCY:FIXED {frequency}'
        self.inst.write(command)
        if len(kwargs) > 0:
            raise NotImplementedError()

    def get_frequency(self):
        """
        Query the frequency of the basic waveform
        :return: frequency (Hz)
        """
        command = f'SOURCE{self.channel}:FREQUENCY:FIXED?'
        frequency = float(self.inst.query(command).strip())
        return frequency

    def set_function(self, **kwargs):    
        raise NotImplementedError()

    def get_function(self):
        raise NotImplementedError()

    def set_harmonic(self, **kwargs):
        raise NotImplementedError()

    def get_harmonic(self):
        raise NotImplementedError()

    def set_modulation(self, **kwargs):
        raise NotImplementedError()

    def get_modulation(self):
        raise NotImplementedError()

    def set_period(self, period):
        """
        Set the period of the basic waveform and the default unit is "s".
        :param float period: seconds
        :return:
        """
        logger.info(f'[set_period] Setting period to {period}')
        command = f'SOURCE{self.channel}:PERIOD {period}'
        self.inst.write(command)

    def get_period(self):
        """
        Query the period of the basic waveform
        :return: period (s)
        """
        command = f'SOURCE{self.channel}:PERIOD?'
        return float(self.inst.query(command).strip())

    def set_phase(self, **kwargs):
        raise NotImplementedError()

    def get_phase(self):
        raise NotImplementedError()

    def set_pulse(self, **kwargs):
        raise NotImplementedError()

    def get_pulse(self):
        raise NotImplementedError()

    def set_sweep(self, **kwargs):
        raise NotImplementedError()

    def get_sweep(self):
        raise NotImplementedError()

    def set_voltage(self, voltage=None, hi=None, lo=None, offset=None, unit=None):
        """
        Set voltage settings
        :param voltage: Set the amplitude of the basic waveform and the default unit is "Vpp".
        :param hi: Set the high level of the basic waveform and the default unit is "V".
        :param lo: Set the low level of the basic waveform and the default unit is "V".
        :param offset: Set the DC offset voltage and the default unit is "VDC".
        :param unit: Set the amplitude unit to VPP, VRMS or DBM.

        :return:
        """
        if voltage and self.max_voltage and voltage > self.max_voltage:
            raise ValueError(f'Requested voltage ({voltage} V) exceeds maximum allowable for '
                             f'channel {self.channel} ({self.max_voltage} V)')
        d = {'LEVEL:IMMEDIATE:AMPLITUDE': voltage,
             'LEVEL:IMMEDIATE:HIGH': hi,
             'LEVEL:IMMEDIATE:LOW': lo,
             'LEVEL:IMMEDIATE:OFFSET': offset,
             'UNIT': unit
             }
        for attr, value in d.items():
            if value is not None:
                command = f'SOURCE{self.channel}:VOLTAGE:{attr} {value}'
                logger.info(f'[set_voltage] {command}')
                self.inst.write(command)

    def get_voltage(self):
        """
        Get voltage settings
        :return: dict of voltage settings
        """
        attrs = ('LEVEL:IMMEDIATE:AMPLITUDE', 'LEVEL:IMMEDIATE:HIGH', 'LEVEL:IMMEDIATE:LOW',
                 'LEVEL:IMMEDIATE:OFFSET', 'UNIT')
        d = {}
        for attr in attrs:
            command = f'SOURCE{self.channel}:VOLTAGE:{attr}?'
            d[attr] = self.inst.query(command).strip()
        setdict = {'voltage': float(d['LEVEL:IMMEDIATE:AMPLITUDE']),
                   'hi': float(d['LEVEL:IMMEDIATE:HIGH']),
                   'low': float(d['LEVEL:IMMEDIATE:LOW']),
                   'offset': float(d['LEVEL:IMMEDIATE:OFFSET']),
                   'unit': d['UNIT']
                   }
        return setdict