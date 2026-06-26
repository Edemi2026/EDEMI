#!/usr/bin/env python3
"""
MPR121 with full init sequence
"""
import smbus2
import time

BUS  = 1
ADDR = 0x5A

def init_mpr121(bus):
    # Soft reset
    bus.write_byte_data(ADDR, 0x80, 0x63)
    time.sleep(0.01)

    # Check device is responding — register 0x5D should be 0x24
    id_val = bus.read_byte_data(ADDR, 0x5D)
    print(f"Chip ID register 0x5D = 0x{id_val:02X} (expect 0x24)")

    # Configure baseline filtering
    bus.write_byte_data(ADDR, 0x2B, 0x01)  # MHD rising
    bus.write_byte_data(ADDR, 0x2C, 0x01)  # NHD rising
    bus.write_byte_data(ADDR, 0x2D, 0x00)  # NCL rising
    bus.write_byte_data(ADDR, 0x2E, 0x00)  # FDL rising
    bus.write_byte_data(ADDR, 0x2F, 0x01)  # MHD falling
    bus.write_byte_data(ADDR, 0x30, 0x01)  # NHD falling
    bus.write_byte_data(ADDR, 0x31, 0xFF)  # NCL falling
    bus.write_byte_data(ADDR, 0x32, 0x02)  # FDL falling

    # Touch/release thresholds for electrodes 0-10
    for i in range(11):
        bus.write_byte_data(ADDR, 0x41 + i * 2, 12)  # touch threshold
        bus.write_byte_data(ADDR, 0x42 + i * 2, 6)   # release threshold

    # Filter config
    bus.write_byte_data(ADDR, 0x5C, 0x10)
    bus.write_byte_data(ADDR, 0x5D, 0x24)  # default charge time

    # Enable 11 electrodes — this starts the chip (ECR register)
    bus.write_byte_data(ADDR, 0x5E, 0x8B)  # run mode, 11 electrodes
    time.sleep(0.05)
    print("MPR121 initialized.")

def read_touch(bus):
    low  = bus.read_byte_data(ADDR, 0x00)
    high = bus.read_byte_data(ADDR, 0x01)
    return low | (high << 8)

with smbus2.SMBus(BUS) as bus:
    init_mpr121(bus)
    print("Press pads. Ctrl+C to exit.\n")
    last = 0
    while True:
        try:
            raw = read_touch(bus)
            if raw != last:
                if raw == 0:
                    print("[RELEASED]")
                else:
                    touched = [f"E{i}" for i in range(11) if raw & (1 << i)]
                    print(f"[TOUCHED]  {touched}  raw=0x{raw:04X}")
                last = raw
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.05)
