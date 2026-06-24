#!/usr/bin/env python3

import sys
import time

from ros2_vesc_control.vesc_uart import VescUart


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 tools/test_set_rpm.py /dev/ttyACM0 5000")
        sys.exit(1)

    port = sys.argv[1]
    erpm = int(sys.argv[2])
    baudrate = 115200

    vesc = VescUart(port, baudrate)

    print(f"Sending {erpm} eRPM to {port}")
    print("CTRL+C to stop")

    try:
        while True:
            vesc.send_erpm(erpm)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nStopping motor")
        for _ in range(20):
            vesc.send_erpm(0)
            time.sleep(0.05)

    finally:
        vesc.close()


if __name__ == "__main__":
    main()