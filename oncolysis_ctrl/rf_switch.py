import logging
import os
import serial
import serial.tools.list_ports
from oncolysis_ctrl import config
import clr
import sys
import time
HERE = os.path.dirname(__file__)
DLL_PATH = os.path.join(HERE, '..', 'dll')
sys.path.append(DLL_PATH)
clr.AddReference('Radiall_USBInterface')
from Radiall_USBInterface import USBInterface

constants = config.constants

VI_FILENAME = os.path.join(HERE, '..', 'LabView', 'RADIALL SPnT USB Interface Controller.vi')
logger = logging.getLogger("oc.rf_switch")


class RFSwitch:
    def __init__(self, comport=None, sn=None, vid=constants.RADIALL_VID, pid=constants.RADIALL_PID):
        """
        RFSwitch constructor
        :param comport: explicit comport (e.g. 'COM3') or None
        :param sn: serial number of USB device (e.g. '31ASW22017741') or None
        :param vid:
        :param pid:
        """
        self.comport = comport
        self.interface = USBInterface()
        self.position = -1
        self.is_open = False
        self.target_port = {'vid': vid, 'pid': pid, 'sn': sn}
        self.port_info = {}

    def open(self):
        """
        Open the connection to the switch
        :return:
        """
        if self.is_open:
            logger.warning('[close] Already connected')
        else:
            logger.info(f'[open] Connecting to RF Switch')
            if self.comport is None: # search for port
                matches = get_comport(vid=self.target_port['vid'], pid=self.target_port['pid'], sn=self.target_port['sn'])
                if len(matches) != 1:
                    msg = f'[open] Found {len(matches)} devices:'
                    for match in matches:
                        comport = match['device']
                        vid = match['vid']
                        pid = match['pid']
                        sn = match['serial_number']
                        msg += '\n' + f"{comport}: (VID={vid}, PID={pid}, SN={sn})"
                    logger.info(msg)
                    raise ConnectionError(f'Found {len(matches)} matching devices for {self.target_port}')
                else:
                    self.port_info = matches[0]
                    self.comport = self.port_info['device']
            connect_ok = self.interface.Initialize(self.comport)
            if not connect_ok:
                raise IOError(f'Could not connect to {self.comport}')
            self.is_open = True
            logger.info(f'[open] Connected to RF Switch  ({self.comport})')

    def set_position(self, position):
        """
        Set position of switch
        :param int position: requested position setting (skip if None)
        :return:
        """
        if position is not None:
            logger.info(f'[set_position] Setting {self.comport} to {position}')
            self.interface.SetPosition(position)
            time.sleep(0.1)
            read_position = self.interface.GetPosition()
            if position != read_position:
                raise IOError(f'[set_position] {self.comport} read back wrong position ({read_position} != {position})')
            else:
                logger.info(f'[set_position] Set {self.comport} to {position}')
            self.position = position

    def get_position(self):
        """
        Get current switch positions
        :return: int switch position
        """
        return self.interface.GetPosition()

    def close(self):
        """
        Close the connection to the switch
        :return:
        """
        if self.is_open:
            close_ok = self.interface.Close()
            if not close_ok:
                raise IOError(f'[close] Failed to close {self.comport}')
            self.is_open = False
            logger.info(f'[close] Disconnected from RF Switch ({self.comport})')
        else:
            logger.warning('[close] Already Disconnected')


def get_comport(vid, pid=None, sn=None):
    """
    Return device name of COM port matching VID and PID
    :param vid: Vendor ID
    :param pid: Product ID (or None)
    :param sn: Serial number (or None)
    :return: array of device info
    """
    port_info = get_port_info()
    matches = []
    for port in port_info:
        if port['vid'] == vid and (pid is None or port['pid'] == pid) and (sn is None or port['serial_number'] == sn):
            matches.append(port)
    return matches


def get_port_info():
    """
    Get all connected COM Ports and structure their info
    :return: list of attribute dictionaries
    """
    attrs = ['description',
             'device',
             'hwid',
             'interface',
             'location',
             'manufacturer',
             'name',
             'pid',
             'product',
             'serial_number',
             'vid']
    ports = serial.tools.list_ports.comports()
    port_info = [{attr: getattr(port, attr) for attr in attrs} for port in ports]
    return port_info
