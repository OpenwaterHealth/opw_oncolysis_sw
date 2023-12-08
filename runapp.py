"""
runapp launches the application with the specified configuration. 

The configuration can be specified using the -config flag, followed by a comma-separated list of configuration IDs. 
The configuration prefixed with an asterisk (*) will be the default configuration, otherwise the first configuration in the list will be the default configuration.

The -simulate flag can be used to run the application in simulation mode, which will not communicate with the hardware.

The -config and -simulate flags can be used in any order. 

Usage: python runapp.py [-s] [-config CONFIG_ID[,CONFIG_ID...]]
"""
import oncolysis_ctrl.config
import sys
import importlib
import ctypes
import os
import datetime
import logging
import sys

HERE = os.path.dirname(__file__)
timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
logpath = os.path.join(HERE, '..', 'logs')
if not os.path.exists(logpath):
    os.makedirs(logpath, exist_ok=True)
logfile = os.path.join(logpath, f'{timestamp}.log')
logfmt = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=logfmt)
logger = logging.getLogger("oc")
fh = logging.FileHandler(logfile)
fh.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '{"time": \"%(asctime)s\", "level": %(levelname)s, "name": \"%(name)s\", "message": \"%(message)s\"}'
)
fh.setFormatter(file_formatter)
logger.addHandler(fh)

# runapp launches the application with the specified configuration. 
# The configuration can be specified using the -config flag, followed by a comma-separated list of configuration IDs. 
# The first configuration ID in the list will be the default configuration.
# The -simulate flag can be used to run the application in simulation mode, which will not communicate with the hardware.
# The -config and -simulate flags can be used in any order. 

if __name__ == "__main__":
    """
    Usage: python runapp.py [-s] [-config CONFIG_ID[,CONFIG_ID...]]
    """
    i = 0
    simulate = False
    config_ids = oncolysis_ctrl.config.CONFIG_IDS
    while i < len(sys.argv):
        if sys.argv[i] in ('-s', '--simulate'):
            simulate = True
            i += 1
        elif sys.argv[i] in ('-config',):
            config_id_list = sys.argv[i+1]
            config_ids = config_id_list.upper().split(',')
            starred = [x[0] == '*' for x in config_ids]
            if any(starred):
                default_idx = starred.index(True)
            else:
                default_idx = 0
            config_ids = [x[1:] if x[0] == '*' else x for x in config_ids]
            oncolysis_ctrl.config.set_config_id(config_ids[default_idx])
            importlib.reload(oncolysis_ctrl.config)
            i += 2
        else:
            i += 1

    import oncolysis_ctrl.app
    from oncolysis_ctrl import rf_switch, function_generator, controller
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
    oncolysis_ctrl.app.runapp(simulate=simulate, config_ids=config_ids)
    while oncolysis_ctrl.config.REBOOT:
        importlib.reload(oncolysis_ctrl.config)
        importlib.reload(oncolysis_ctrl.app)
        for module in (rf_switch, function_generator, controller):
            importlib.reload(module)
        oncolysis_ctrl.app.runapp(simulate=simulate, config_ids=config_ids)

