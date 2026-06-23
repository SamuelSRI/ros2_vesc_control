import time

import serial

from rover_vesc_control.vesc_protocol import (
    make_set_rpm_packet,
    make_get_values_packet,
    extract_packet,
    parse_get_values_payload,
)


class VescUart:
    def __init__(self, port: str, baudrate: int, timeout: float = 0.02):
        self.port = port
        self.baudrate = baudrate

        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )

    def send_erpm(self, erpm: int):
        packet = make_set_rpm_packet(erpm)
        self.serial.write(packet)

    def read_values(self):
        """
        Même méthode que ton test qui fonctionne :
        - reset input buffer
        - envoie COMM_GET_VALUES
        - lit la réponse
        - parse les valeurs
        """

        try:
            self.serial.reset_input_buffer()
            self.serial.write(make_get_values_packet())

            time.sleep(0.01)

            raw_data = self.serial.read(256)
            payload = extract_packet(raw_data)

            if payload is None:
                return None

            return parse_get_values_payload(payload)

        except serial.SerialException:
            return None

    def close(self):
        if self.serial.is_open:
            self.serial.close()