# modbus_utils.py

import serial
import time
import logging

# --- Configuration ---
SERIAL_PORT = "COM6"
BAUD_RATE = 9600
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
DATA_BITS = 8
TIMEOUT = 1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_crc(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder='little')

def generate_write_command(slave_id: int, register: int, value: int) -> bytes:

    # Function code for Write Single Register is 0x06
    function_code = 6

    # Register address starts from 0, so we subtract 1
    #register_address = register - 1

    # [Slave ID] [Function Code] [Register Address High] [Register Address Low] [Value High] [Value Low]
    command = bytearray()
    command.append(slave_id)
    command.append(function_code)
    command.append(register >> 8)    # High byte of register
    command.append(register & 0xFF) # Low byte of register
    command.append(value >> 8)              # High byte of value
    command.append(value & 0xFF)            # Low byte of value

    crc = calculate_crc(command)
    command.extend(crc)

    return bytes(command)

def send_modbus_command(command: bytes):
    try:
        with serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUD_RATE,
            parity=PARITY,
            stopbits=STOP_BITS,
            bytesize=DATA_BITS,
            timeout=TIMEOUT
        ) as ser:
            logging.info(f"Connecting to {ser.portstr}")
            if not ser.is_open:
                ser.open()

            logging.info(f"Sending command: {command.hex().upper()}")
            ser.write(command)
            time.sleep(0.1)
            logging.info("Command sent successfully.")
            return True

    except serial.SerialException as e:
        logging.error(f"Serial port error: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return False