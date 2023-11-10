from binascii import hexlify
import time
import serial


class JrtSerial:
    AUTO_BAUD = b'\x55'

    def __init__(self, port, baud=None, address=0, debug=False):
        if baud is None:
            baud = 19200

        self.debug = debug

        self.address = address
        self.baud = baud
        self.serial = serial.Serial(port, baud, rtscts=True)
        self.serial.setRTS(1)
        time.sleep(0.5)
        self.serial.setRTS(0)
        self.auto_baud()
        self.last_signal_quality = None

    def auto_baud(self):
        """Automatically the baud rate of the sensor to the baud rate of the serial port."""
        while True:
            self.serial.write(self.AUTO_BAUD)
            try:
                r = self.serial.read(1)
            except serial.serialutil.SerialException:
                continue
            if self.debug:
                print('auto_baud received: ' + hexlify(r).decode('ascii'))
            if r == b'\x00':
                if self.debug:
                    print('auto baud success')
                return True
            else:
                return False

    def checksum(self, body):
        """Calculate the checksum of a command or response."""
        if self.debug:
            print('checksumming: ' + hexlify(body).decode('ascii'))
        cksum = 0
        for c in body:
            cksum += c
        return cksum & 0xff

    def send_cmd(self, cmd):
        """Send a command to the sensor."""
        cmd = b'\xAA' + cmd + self.checksum(cmd).to_bytes(1, 'big', signed=False)
        if self.debug:
            print('sending: ' + hexlify(cmd).decode('ascii'))
        self.serial.write(cmd)

    def read_response(self, register=None):
        """Read a response from the sensor."""
        hdr = self.serial.read(1)
        if self.debug:
            print(b'header: ' + hexlify(hdr))
        while hdr != b'\xAA' and hdr != b'\xEE':
            hdr = self.serial.read(1)
            print(b'header: ' + hexlify(hdr))

        address = self.serial.read(1)
        response_register = self.serial.read(2)
        response_register_int = int.from_bytes(response_register, 'big', signed=False)
        payload_length = self.serial.read(2)
        payload = self.serial.read(int.from_bytes(payload_length, 'big') + 1)
        if response_register_int == 0x22:
            signal_quality = self.serial.read(2)
            signal_quality_int = int.from_bytes(signal_quality, 'big', signed=False)
            self.last_signal_quality = signal_quality_int
        else:
            signal_quality = b''
            signal_quality_int = None

        cksum = self.serial.read(1)

        response = address + response_register + payload_length + payload + signal_quality

        if self.debug:
            print(
                f"response was: {hexlify(response).decode('ascii')} {signal_quality_int} {response_register_int} {payload_length} {payload}")

        response_cksum = self.checksum(response)

        if cksum != response_cksum.to_bytes(1, "big"):
            if self.debug:
                print(f'checksum mismatch {hexlify(cksum)} != {hexlify(response_cksum.to_bytes(1, "big"))}')
            raise Exception('Invalid checksum')

        if register is not None:
            if response_register_int != register and (response_register_int != 0x22 and register != 0x20):
                if self.debug:
                    print(f'response register mismatch {response_register_int} != {register}')
                raise Exception('Invalid register')

        if hdr == b'\xEE':
            raise Exception('Error response')

        return int.from_bytes(payload, 'big', signed=True)


    def write_register(self, register, value):
        """Write a value to a register."""
        if self.debug:
            print(f'writing register {register} with value {value}')

        payload_count = (1).to_bytes(2, 'big', signed=False)

        value = value.to_bytes(2, 'big', signed=True)

        cmd = self.address.to_bytes(1, 'big', signed=False) + register.to_bytes(2, 'big',
                                                                                signed=False) + payload_count + value

        self.send_cmd(cmd)
        return self.read_response(register)

    def read_register(self, register):
        """Read a register."""
        if self.debug:
            print(f'reading register {register}')

        cmd = (self.address | 0x80).to_bytes(1, 'big', signed=False) + register.to_bytes(2, 'big', signed=False)

        self.send_cmd(cmd)
        return self.read_response(register)


    def set_laser(self, enable=True):
        """Enable or disable the laser."""
        if enable:
            value = 1
        else:
            value = 0
        return self.write_register(0x1be, value)

    def read_hw_version(self):
        """Read the hardware version of the sensor."""
        return self.read_register(0x0A)

    def read_sw_version(self):
        """Read the software version of the sensor."""
        return self.read_register(0x0c)

    def read_status(self):
        """Read the status of the sensor."""
        return self.read_register(0x00)

    def status_to_text(self, status):
        """Convert a status code to a human-readable string."""
        if status == 0:
            return 'No error'
        elif status == 1:
            return 'Power too low'
        elif status == 2:
            return 'Internal error; ignore'
        elif status == 3:
            return 'Module temperature too low'
        elif status == 4:
            return 'Module temperature too high'
        elif status == 5:
            return 'Target out of range'
        elif status == 6:
            return 'Invalid measure result'
        elif status == 7:
            return 'Background light too strong'
        elif status == 8:
            return 'Laesr signal too weak'
        elif status == 9:
            return 'Laser signal too strong'
        elif status == 10:
            return 'Hardware fault 1'
        elif status == 11:
            return 'Hardware fault 2'
        elif status == 12:
            return 'Hardware fault 3'
        elif status == 13:
            return 'Hardware fault 4'
        elif status == 14:
            return 'Hardware fault 5'
        elif status == 15:
            return 'Laser signal not stable'
        elif status == 16:
            return 'Hardware fault 6'
        elif status == 17:
            return 'Hardware fault 7'
        elif status == 0x81:
            return 'Invalid frame'
        else:
            return 'UNKNOWN'

    def start_continuous_measurement(self, mode='auto'):
        """Start continuous measurement with the sensor; use read_measurement() to poll for measurement results."""
        if mode == 'fast':
            return self.write_register(0x20, 6)
        elif mode == 'slow':
            return self.write_register(0x20, 5)
        else:  # auto
            return self.write_register(0x20, 4)

    def read_measurement(self):
        """Read a measurement from the sensor; use start_continuous_measurement() to start continuous measurement."""
        return self.read_response(0x22)

    def stop_continuous_measurement(self):
        """Stop continuous measurement."""
        self.serial.write(b'X')

    def one_shot_measurement(self, mode='auto'):
        """Perform a single measurement and return the result -- measurement can be done in auto, fast, or slow modes."""
        if mode == 'fast':
            return self.write_register(0x20, 2)
        elif mode == 'slow':
            return self.write_register(0x20, 1)
        else:
            return self.write_register(0x20, 0)

    def read_input_voltage(self):
        """Read the input voltage to the sensor -- this is encoded in millivolts (0x3300 is 3.3 volts)."""
        return self.read_register(0x06)


