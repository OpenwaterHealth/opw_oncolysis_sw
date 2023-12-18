"""
Configuration Constants

Module containing constants for the oncolysis_ctrl package.
"""

import importlib
import os

DEFAULT_CONFIG = 'invitro_8mm'
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILENAME = os.path.join(HERE, 'CONFIG_ID.txt')
CONFIG_IDS = ('INVITRO_5MM', 'INVITRO_7MM', 'INVITRO_8MM', 'INVITRO_9MM', 'INVIVO_FLANK')


def get_constants(cid=DEFAULT_CONFIG):
    """
    Get the constants for the specified configuration ID.

    :param cid: The configuration ID to get constants for.
    :return: The constants module for the specified configuration ID.
    """
    return importlib.import_module(f'oncolysis_ctrl.configurations.constants_{cid.lower()}')


def get_config_id():
    """
    Get the current configuration ID.
    
    Loads the current configuration ID from the CONFIG_ID.txt.
    If the file does not exist, create it with the default configuration ID.
    :return: The current configuration ID.
    """
    if not os.path.exists(CONFIG_FILENAME):
        set_config_id(DEFAULT_CONFIG)
    with open(CONFIG_FILENAME, 'r') as f:
        cid = f.read()
    return cid.strip().upper()


def set_config_id(cid):
    """
    Set the current configuration ID.
    
    Writes the current configuration ID to the CONFIG_ID.txt file.
    :param cid: The configuration ID to set.
    :return: None
    """
    with open(CONFIG_FILENAME, 'w') as f:
        f.write(cid)


CONFIG_NAMES = []
for config_id in CONFIG_IDS:
    constants = get_constants(config_id)
    CONFIG_NAMES.append(constants.NAME)
CONFIG_NAMES = tuple(CONFIG_NAMES)

config_id = get_config_id()
constants = get_constants(config_id)
REBOOT = False
