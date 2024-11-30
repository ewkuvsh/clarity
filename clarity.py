import asyncio
import aioble
import bluetooth

# Define the Service and Characteristic UUIDs (must match the peripheral)
SERVICE_UUID = bluetooth.UUID('831c0e71-708a-4c5c-86ef-a71d64ad66ee')
CHARACTERISTIC_UUID = bluetooth.UUID('831c0e71-708a-4c5c-86ef-a71d64ad66ee')

async def scan_and_connect():
    print("Scanning for peripherals...")
    async with aioble.scan(5000) as scanner:  # Scan for 5 seconds
        async for result in scanner:
            print("Found device:", result.name(), result.addr_hex())
            # Check for the target peripheral
            if result.name() == "Nicla":
                print("Connecting to:", result.addr_hex())
                device = await result.connect()
                print("Connected to device:", device)
                return device
    return None

async def main():
    # Scan and connect to the peripheral
    device = await scan_and_connect()
    if not device:
        print("Peripheral not found.")
        return

    # Discover services and characteristics
    print("Discovering services...")
    service = await device.service(SERVICE_UUID)
    print("Discovered service:", service)

    characteristic = await service.characteristic(CHARACTERISTIC_UUID)
    print("Discovered characteristic:", characteristic)

    # Subscribe to notifications
    print("Subscribing to notifications...")
    await characteristic.subscribe()

    # Wait for notifications
    while True:
        print("Waiting for data...")
        data = await characteristic.notified()
        print("Received:", data.decode())  # Decode binary data into string

asyncio.run(main())
