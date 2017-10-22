# !/usr/bin/env python
# -*- coding: utf-8 -*-
import sublime

from time import sleep
from ..tools import pyserial
from ..tools import SETTINGS_NAME
from .pyserial.tools import list_ports

in_use = []
serial_dict = {}
setting_key = 'serial_ports'


class Serial:

    def __init__(self, port, baudrate=115200, timeout=1):
        self._serial = pyserial.Serial()
        self._serial.port = port
        self._serial.baudrate = baudrate
        self._serial.timeout = timeout

        self._stop_task = True

    def open(self):
        """Open port

        Opens the port given in the construct.
        _stop_task:     is used to avoid an error when it's closed.
        in_use:         list of port already open
        serial_dict:    dictionary with the serial object
        """
        self._serial.open()
        self._stop_task = False

        # store port used
        port = self._serial.port
        in_use.append(port)
        serial_dict[port] = self

    def receive(self):
        """Receive data

        Receive the data from the selected port

        Returns:
            bytes -- Bytes read from the port
        """
        return self._serial.readline()

    def readable(self):
        """Convert data from byte to string

        Returns in a readable characters/string the byte data received in
        the serial port. It will also replace the end lines to be compatible
        with the Sublime Text end lines (\n)

        Returns:
            str -- readable received data
        """
        data = self.receive()
        data = data.decode('utf-8', 'replace')
        data = data.replace('\r\n', '\n'). replace('\r', '\n')
        return data

    def is_running(self):
        """Check if the port is running

        This method will be set to false before the port is closed, it will
        avoid to get the overlaped error, when the is_open object is used

        Returns:
            bool -- True if the port is running (open) false if not
        """
        return not self._stop_task

    def write(self, data):
        """Write bytedata to the port

        Writes bytedata to the selected serial port

        Arguments:
            data {byte} -- data to send

        Returns:
            int -- Number of bytes written.
        """
        return self._serial.write(data)

    def writable(self, data, line_ending='\r\n'):
        """Write bytes from string

        Writes bytes in the selected port from the readable string sent

        Arguments:
            data {str} -- data to send

        Returns:
            int -- Number of bytes written.
        """
        data += line_ending
        data = data.encode('utf-8', 'replace')

        return self._serial.write(data)

    def keep_listen(self, printer):
        """Listen port

        Listen for new data in the selected port

        Arguments:
            printer {obj} -- function or method to print the data
        """
        while(self.is_running()):
            data = self.readable()
            if(not printer):
                break
            printer(data)

    def close(self):
        """Close serial connection

        Closes the serial connection in the port selected.
        _stop_task will be updated before close the port to avoid the overlaped
        error,
        """
        self._stop_task = True
        self._serial.close()

        port = self._serial.port

        in_use.remove(port)
        del serial_dict[port]


def ports_list():
    """List of serial ports

    Return the list of serial ports availables on the system.

    Returns:
        [list/list] -- list of list like [['port1 fullname',
                       port_name]['port2 fullname', 'port_name']]
    """
    ports = list(list_ports.comports())
    dev_names = ['ttyACM', 'ttyUSB', 'tty.', 'cu.']

    serial_ports = []
    for port_no, description, address in ports:
        for dev_name in dev_names:
            if(address != 'n/a' and
                    dev_name in port_no or sublime.platform() == 'windows'):
                serial_ports.append([description, port_no])
                break

    return serial_ports


def check_port(port):
    """Check serial port

    Checks if the given serial port exits or if isn't busy

    Arguments:
        port {str} -- serial port name

    Returns:
        bool -- True if exist/not busy False if not
    """
    serial = pyserial.Serial()
    serial.port = port

    try:
        serial.open()
    except pyserial.serialutil.SerialException as e:
        if('PermissionError' in str(e)):
            print("Your port is busy")
            return False
        elif('FileNotFoundError' in str(e)):
            print("Port not found")
            return False
    return True


def selected_port(request_port=False):
    """Get serial port

    If there is only one port available, it will be automatically used,
    even if it is not in the preferences, if there is more than one port,
    the user selection will be used, if not setting stored or it's outdated
    one, the user will prompted to select one.

    Keyword Arguments:
        request_port {bool} -- True: show the quick panel to select a port if
                        there no selection or the selected one is not avaialble
                        anymore (default: {False})

    Returns:
        str -- selected port, false with any problem
    """
    ports = ports_list()
    if(ports):
        items = []
        for port in ports:
            items.append(port[1])
        ports = items

    settings = sublime.load_settings(SETTINGS_NAME)
    port_setting = settings.get(setting_key, None)

    if(ports and len(ports) == 1):
        return ports[0]
    elif(ports and len(ports) == 0):
        return False
    elif(not port_setting):
        if(request_port):
            sublime.active_window().run_command('upiot_select_port')
        return False
    elif(port_setting not in ports):
        if(request_port):
            sublime.active_window().run_command('upiot_select_port')
        return False

    return port_setting