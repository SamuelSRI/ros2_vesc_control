import struct


COMM_GET_VALUES = 4
COMM_SET_RPM = 8


def crc16(data: bytes) -> int:
    crc = 0

    for b in data:
        crc ^= b << 8

        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF

    return crc


def make_packet(payload: bytes) -> bytes:
    """
    Format paquet court VESC :
    0x02 | length | payload | crc_high | crc_low | 0x03
    """

    if len(payload) > 255:
        raise ValueError("Payload too long for short VESC packet")

    crc = crc16(payload)

    return (
        bytes([2, len(payload)])
        + payload
        + bytes([(crc >> 8) & 0xFF, crc & 0xFF, 3])
    )


def make_set_rpm_packet(erpm: int) -> bytes:
    payload = bytes([COMM_SET_RPM]) + struct.pack(">i", int(erpm))
    return make_packet(payload)


def make_get_values_packet() -> bytes:
    return make_packet(bytes([COMM_GET_VALUES]))


def extract_packet(buffer: bytes):
    """
    Cherche un paquet VESC complet dans un buffer.
    Retourne le payload si le CRC est bon, sinon None.
    """

    if len(buffer) < 5:
        return None

    start_index = buffer.find(bytes([2]))

    if start_index < 0:
        return None

    buffer = buffer[start_index:]

    if len(buffer) < 5:
        return None

    payload_len = buffer[1]
    total_len = 2 + payload_len + 2 + 1

    if len(buffer) < total_len:
        return None

    packet = buffer[:total_len]

    if packet[-1] != 3:
        return None

    payload = packet[2:2 + payload_len]

    received_crc = (packet[2 + payload_len] << 8) | packet[2 + payload_len + 1]
    calculated_crc = crc16(payload)

    if received_crc != calculated_crc:
        return None

    return payload


def parse_get_values_payload(payload: bytes):
    """
    Parse la réponse COMM_GET_VALUES.

    rpm est en eRPM, pas en RPM roue.
    """

    if payload is None:
        return None

    if len(payload) < 55:
        return None

    if payload[0] != COMM_GET_VALUES:
        return None

    index = 1

    def get_int16(scale=1.0):
        nonlocal index
        value = struct.unpack(">h", payload[index:index + 2])[0]
        index += 2
        return value / scale

    def get_int32(scale=1.0):
        nonlocal index
        value = struct.unpack(">i", payload[index:index + 4])[0]
        index += 4
        return value / scale

    def get_uint8():
        nonlocal index
        value = payload[index]
        index += 1
        return value

    temp_mos = get_int16(10.0)
    temp_motor = get_int16(10.0)

    current_motor = get_int32(100.0)
    current_in = get_int32(100.0)

    id_current = get_int32(100.0)
    iq_current = get_int32(100.0)

    duty = get_int16(1000.0)

    rpm = get_int32(1.0)

    v_in = get_int16(10.0)

    amp_hours = get_int32(10000.0)
    amp_hours_charged = get_int32(10000.0)

    watt_hours = get_int32(10000.0)
    watt_hours_charged = get_int32(10000.0)

    tachometer = int(get_int32(1.0))
    tachometer_abs = int(get_int32(1.0))

    fault_code = get_uint8()

    return {
        "temp_mos": temp_mos,
        "temp_motor": temp_motor,
        "current_motor": current_motor,
        "current_in": current_in,
        "id_current": id_current,
        "iq_current": iq_current,
        "duty": duty,
        "rpm": rpm,
        "v_in": v_in,
        "amp_hours": amp_hours,
        "amp_hours_charged": amp_hours_charged,
        "watt_hours": watt_hours,
        "watt_hours_charged": watt_hours_charged,
        "tachometer": tachometer,
        "tachometer_abs": tachometer_abs,
        "fault_code": fault_code,
    }