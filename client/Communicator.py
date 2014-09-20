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

    class CommunicationFaultException(Exception):
        """
        Exception for communication problems
        """

        def __init__(self, expectedMsg, msg):
            """
            constructor

            @param expectedMsg excepted content of the message
            @param msg the content of the message you got
            """
            super().__init__(self,
                             'Expected content: "{0}" | Content you got: "{1}"'
                             .format(expectedMsg, msg))

    class CompressedClipTooLong(Exception):
        """
        Exception for too long clips
        """

        def __init__(self):
            """
            constructor
            """
            super().__init__(self, 'Compressed clip is too long!')

    serialPort = None

    @classmethod
    def getPorts(cls):
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
                if pong == b'nsd1':
                    result.append(port)
            except serial.SerialTimeoutException:
                pass
        return result

    @classmethod
    def start(cls, port):
        """
        Starts a transmission.

        @param port port of the Nightsky device
        @raise CommunicationFaultException when the helo response is wrong
        """
        cls.serialPort = serial.Serial(port)
        time.sleep(2)  # Sleep for windows
        cls.serialPort.write(b'helo')
        heloResp = cls.serialPort.read(4)
        if heloResp != b'helo':
            cls.serialPort.close()
            raise cls.CommunicationFaultException(b'helo', heloResp)

    @classmethod
    def transmitFrame(cls, frame):
        """
        Transmits a frame.

        @param frame compressed frame as bytes
        """
        cls.serialPort.write(frame)
        resp = cls.serialPort.read(4)
        print(resp)
        if resp == b'done':
            raise cls.CompressedClipTooLong()
        if resp != b'ok':
            raise cls.CommunicationFaultException(b'ok', resp)

    @classmethod
    def end(cls):
        """
        Ends the transmission.
        """
        cls.serialPort.write(b'\x00\x00')
        doneResp = cls.serialPort.read(4)  # Wait for "done" from device
        cls.serialPort.close()
        print(doneResp)
        if doneResp != b'done':
            raise cls.CommunicationFaultException(b'done', doneResp)
