"""
Communication class
"""
import sys
import glob
import serial
import time


class Communicator:
    """
    Class that's responsible for communication with the arduino
    """

    def __init__(self):
        """
        constructor
        """
        pass

    def getPorts(self):
        """
        returns a list of available serial ports

        @return a list with available ports
        @see https://stackoverflow.com/questions/12090503/listing-available-
            com-ports-with-python
        """
        if sys.platform.startswith('win'):
            ports = ['COM' + str(i + 1) for i in range(256)]

        elif sys.platform.startswith('linux') or sys.platform.startswith(
                'cygwin'):
            # this is to exclude your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')

        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')

        else:
            raise EnvironmentError('Unsupported platform')

        possiblePorts = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                possiblePorts.append(port)
            except (OSError, serial.SerialException):
                pass

        result = []
        for port in possiblePorts:
            try:
                s = serial.Serial(port, 9600, timeout=2, writeTimeout=2)
                time.sleep(2)  # Sleep for windows
                s.write(b'ping')
                pong = s.read(4)
                if pong == b'nsp1':
                    result.append(port)
            except serial.SerialTimeoutException:
                pass
        return possiblePorts
