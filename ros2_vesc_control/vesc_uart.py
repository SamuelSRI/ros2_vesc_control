import time

import serial

from ros2_vesc_control.vesc_protocol import (
    make_set_rpm_packet,
    make_get_values_packet,
    extract_packet,
    parse_get_values_payload,
)


class VescUart:
    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float = 0.02,
        reconnect_period: float = 2.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.reconnect_period = reconnect_period

        self.serial = None
        self.last_reconnect_attempt = 0.0

        # Try once at startup, but do not crash if the port does not exist.
        self.try_connect(force=True)

    def is_connected(self) -> bool:
        return self.serial is not None and self.serial.is_open

    def try_connect(self, force: bool = False) -> bool:
        """
        Try to connect to the VESC serial port.

        Returns:
            True if connected
            False if the port is not available
        """

        if self.is_connected():
            return True

        now = time.time()

        if not force and (now - self.last_reconnect_attempt) < self.reconnect_period:
            return False

        self.last_reconnect_attempt = now

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            return True

        except (serial.SerialException, OSError):
            self.serial = None
            return False

    def send_erpm(self, erpm: int) -> bool:
        """
        Send an eRPM command to the VESC.

        Returns:
            True if the command was sent
            False if the VESC is not connected
        """

        if not self.try_connect():
            return False

        try:
            packet = make_set_rpm_packet(erpm)
            self.serial.write(packet)
            return True

        except (serial.SerialException, OSError):
            self.close()
            return False

    def read_values(self):
        """
        Read VESC values using the same logic as the working test:
        - reset input buffer
        - send COMM_GET_VALUES
        - read response
        - extract packet
        - parse values

        Returns:
            Parsed values if successful
            None if disconnected, invalid response, or read error
        """

        if not self.try_connect():
            return None

        try:
            self.serial.reset_input_buffer()
            self.serial.write(make_get_values_packet())

            time.sleep(0.01)

            raw_data = self.serial.read(256)
            payload = extract_packet(raw_data)

            if payload is None:
                return None

            return parse_get_values_payload(payload)

        except (serial.SerialException, OSError):
            self.close()
            return None

    def close(self):
        if self.serial is not None:
            try:
                if self.serial.is_open:
                    self.serial.close()
            except (serial.SerialException, OSError):
                pass

        self.serial = None