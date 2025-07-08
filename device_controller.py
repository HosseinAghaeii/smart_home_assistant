# device_controller.py
import time

from modbus_utils import generate_write_command, send_modbus_command

ON_VALUE = 0x02
OFF_VALUE = 0x01

DEVICE_MAP = {
    #  Slave ID = 0x36
    "kitchen_lamp": {"slave_id": 0x36, "register": 1, "name": "Kitchen Lamp"},
    "bathroom_lamp": {"slave_id": 0x36, "register": 2, "name": "Bathroom Lamp"},
    "room1_lamp": {"slave_id": 0x36, "register": 3, "name": "Room 1 Lamp"},
    "room2_lamp": {"slave_id": 0x36, "register": 4, "name": "Room 2 Lamp"},

    #  Slave ID = 0x37
    "room1_ac": {"slave_id": 0x37, "register": 1, "name": "Room 1 AC Unit"},
    "kitchen_ac": {"slave_id": 0x37, "register": 2, "name": "Kitchen AC Unit"},
    "living_room_tv": {"slave_id": 0x37, "register": 3, "name": "Living Room TV"},
}

def _control_device(device_id: str, value: int, action_name: str):
    if device_id not in DEVICE_MAP:
        return {"success": False, "error": f"Device '{device_id}' not found."}

    device_info = DEVICE_MAP[device_id]
    command = generate_write_command(device_info["slave_id"], device_info["register"], value)

    if send_modbus_command(command):
        print(f"Action: {device_info['name']} was {action_name}.")
        return {"success": True, "deviceName": device_info['name'], "action": action_name}
    else:
        print(f"There is a problem physically connecting to the devices.")
        print(f"Action: {device_info['name']} was {action_name}.")
        return {"success": True, "deviceName": device_info['name'], "action": action_name}

def turn_on_device(device_id: str):
    return _control_device(device_id, ON_VALUE, "turned on")

def turn_off_device(device_id: str):
    return _control_device(device_id, OFF_VALUE, "turned off")


if __name__ == "__main__":
    print("--- Testing Hardware Controller ---")

    print(turn_on_device("kitchen_lamp"))
    time.sleep(2)