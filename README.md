# JRT Laser Distance Sensor Python Library

This library is a Python library for the JRT laser distance sensor for laser devices from Chengdu JRT Meter Technology Company, Ltd.

This library has been tested with the following sensors:

* U81B (https://www.jrt-measure.com/industrial-laser-distance-sensor/55121160.html)

The author of this library has no affiliation with Chengdu JRT and this library is not endorsed by Chengdu JRT.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install jrt-laser-distance-sensor.

```bash
pip install jrt_laser_distance_sensor
```

After installation, you should be able to test the library with the following command:

```bash
jrt-laser-distance-sensor <serial-port-name>
```

Serial port naming conventions vary by platform (e.g. /dev/ttyUSB0 on Linux, COM1 on Windows, /dev/tty.usb-12345 on OS X).

All measurements from the library are reported in millimeters.

## Usage

A simple example of using the library is as follows, with the sensor connected to /dev/ttyUSB0:

```python
from jrt_laser_distance_sensor import JrtSerial

sensor = JrtSerial('/dev/ttyUSB0')
print(sensor.one_shot_measurement())
```

You can also do continuous measurements:

```python
from jrt_laser_distance_sensor import JrtSerial

sensor = JrtSerial('/dev/ttyUSB0')

sensor.start_continuous_measurement()

while True:
    print(sensor.read_measurement())
```

This is block of code demonstrates most of the useful features of the library:

```python
import sys
import time
from binascii import hexlify
from jrt_laser_distance_sensor import JrtSerial

def main():
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        print(f'usage: {sys.argv[0]} <port>')
        sys.exit(1)
    jrt = JrtSerial(port)
    hw_version = hexlify(jrt.read_hw_version().to_bytes(2, 'big', signed=True))
    print(f'hw version: {hw_version}')
    sw_version = hexlify(jrt.read_sw_version().to_bytes(2, 'big', signed=True))
    print(f'sw version: {sw_version}')
    input_voltage= hexlify(jrt.read_input_voltage().to_bytes(2, 'big', signed=True))
    print(f'input voltage: {input_voltage}')
    print(f"reading status: {jrt.status_to_text(jrt.read_status())}")
    print("testing laser on / off")
    print('laser', jrt.set_laser(True))
    print('laser should be on (sleeping 2 seconds)')
    time.sleep(2)
    print('laser', jrt.set_laser(False))
    print('laser should be off (sleeping 2 seconds)')
    time.sleep(2)

    print('testing continuous measurement in auto mode (10 readings)')
    jrt.start_continuous_measurement('auto')
    x = 0
    while x < 10:
        print(f"{x + 1}: {jrt.read_measurement()} (signal quality: {jrt.last_signal_quality})")
        time.sleep(0.1)
        x += 1

    jrt.stop_continuous_measurement()

    print('continuous measurement test finished')
    time.sleep(0.5)
    print('test one shot measurement')

    print('auto', jrt.one_shot_measurement('auto'))
    print('slow', jrt.one_shot_measurement('slow'))
    print('fast', jrt.one_shot_measurement('fast'))

    print('turning laser off')
    print('laser', jrt.set_laser(False))
```

It should produce output similar to the following:

```text
hw version: b'8301'
sw version: b'1b08'
input voltage: b'3303'
reading status: No error
testing laser on / off
laser 1
laser should be on (sleeping 2 seconds)
laser 0
laser should be off (sleeping 2 seconds)
testing continuous measurement in auto mode (10 readings)
1: 271 (signal quality: 98)
2: 271 (signal quality: 97)
3: 270 (signal quality: 108)
4: 270 (signal quality: 110)
5: 270 (signal quality: 83)
6: 270 (signal quality: 81)
7: 270 (signal quality: 87)
8: 271 (signal quality: 83)
9: 270 (signal quality: 87)
10: 270 (signal quality: 103)
continuous measurement test finished
test one shot measurement
auto 271
slow 271
fast 270
turning laser off
laser 0
```