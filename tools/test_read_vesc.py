#!/usr/bin/env python3

import sys
import time

from rover_vesc_control.vesc_uart import VescUart


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/test_read_vesc.py /dev/ttyACM0")
        sys.exit(1)

    port = sys.argv[1]
    baudrate = 115200

    vesc = VescUart(port, baudrate)

    print(f"Reading VESC values from {port}")
    print("CTRL+C to stop")

    try:
        while True:
            values = vesc.read_values()

            if values is None:
                print("No response")
            else:
                print(
                    f"rpm/eRPM={values['rpm']:.0f} | "
                    f"vin={values['v_in']:.1f} V | "
                    f"duty={values['duty']:.3f} | "
                    f"current_motor={values['current_motor']:.2f} A | "
                    f"temp_mos={values['temp_mos']:.1f} °C | "
                    f"fault={values['fault_code']}"
                )

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping")

    finally:
        vesc.close()


if __name__ == "__main__":
    main()