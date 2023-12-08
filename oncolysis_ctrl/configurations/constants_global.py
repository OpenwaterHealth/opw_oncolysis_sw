ID = ''
NAME = ''
AMPLIFIER_GAIN = 562.3
POWER_MODE = 'constant_mi'
POWER_MODES = ('constant_mi', 'constant_pressure', 'constant_isppa', 'constant_ispta', 'constant_ispta_mi100')
POWER_SETTINGS = {
    'constant_pressure': {
        'units': 'kPa',
        'label': 'Constant Pressure',
        'minmax': (0, 1000),
        'step': 25,
        'default': 750},
    'constant_mi': {
        'units': '%',
        'label': 'Constant MI',
        'minmax': (0, 200),
        'step': 5,
        'default': 100},
    'constant_ispta': {
        'units': 'mW/cm2',
        'label': 'Constant ISPTA (Adjusted MI)',
        'minmax': (0, 1000),
        'step': 10,
        'default': 720},
    'constant_ispta_mi100': {
        'units': 'mW/cm2',
        'label': 'Constant ISPTA (Adjusted Burst Length)',
        'minmax': (0, 1000),
        'step': 10,
        'default': 720},
    'constant_isppa': {
        'units': 'W/cm2',
        'label': 'Constant ISPPA',
        'minmax': (0, 100),
        'step': 1,
        'default': 50}}


DURATIONS_S = (5, 30, 60 * 1, 60 * 2, 60 * 5, 60 * 10, 60 * 15)
DURATION_S = 120

FREQUENCIES_KHZ = (70, 100, 150, 230, 300, 500, 670, 1000)
FREQUENCY_KHZ = 70

CALIB = {  70: {'p_ref': 502.693,
                'coeff_a': 0.00025164,
                'coeff_b': 0.930838},
           100: {'p_ref': 600.833,
                 'coeff_a': 4.88529e-05,
                 'coeff_b': 1.67454},
           150: {'p_ref': 735.867,
                 'coeff_a': 0.00239558,
                 'coeff_b': 1.37781},
           230: {'p_ref': 911.208,
                 'coeff_a': 0.00135768,
                 'coeff_b': 2.70039},
           300: {'p_ref': 1040.67,
                 'coeff_a': 0.00410544,
                 'coeff_b': 3.62235},
           500: {'p_ref': 1343.5,
                 'coeff_a': 0.00373053,
                 'coeff_b': 3.94092},
           670: {'p_ref': 1555.22,
                 'coeff_a': 0.00589971,
                 'coeff_b': 5.12642},
           1000: {'p_ref': 1900,
                  'coeff_a': 0.00153149,
                  'coeff_b': 8.46851}}

# RF Switch
RADIALL_VID = 0x10C4
RADIALL_PID = 0xEA71
RADIALL_SN = ('31ASW22007189',)

RF_SWITCH_SETTINGS = {70: (1,),
                      100: (2,),
                      150: (3,),
                      230: (4,),
                      300: (5,),
                      500: (6,),
                      670: (7,),
                      1000: (8,)}

# Function Generator
RIGOL_DG4162_VID = 0x1AB1
RIGOL_DG4162_PID = 0x0641
CHANNELS = (1, 2)

MAX_VOLTAGE = 1.5
TRANSMIT_CHANNEL = 1
BURST_PERIOD = 0.4
BURST_LENGTHS = (.002, .01, .02, .03, .04)
BURST_LENGTH = .04
BURST_DUTY_CYCLES = (.005, 0.01, 0.02, 0.05, 0.1)
BURST_DUTY_CYCLE = 0.1
BURST_PARAMS_TEMPLATE = {'enabled': True,
                         'period': 0.1,
                         'mode': 'TRIG',
                         'cycles': 1,
                         'phase': 0,
                         'delay': 0,
                         'trig_negative': False,
                         'trig_source': 'INT',
                         'trig_out_en': True,
                         'trig_out_negative': False,
                         'gate_invert': False}

SOURCE_PARAMS_TEMPLATE = {'mode': 'SIN',
                          'frequency': 100,
                          'amplitude': 0,
                          'offset': 0,
                          'phase': 0}
