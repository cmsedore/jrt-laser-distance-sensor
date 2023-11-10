import sys
import time
from binascii import hexlify
import sys
from .jrtserial import JrtSerial


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
        print(f"{x + 1}: {jrt.read_response()} (signal quality: {jrt.last_signal_quality})")
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