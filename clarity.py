import asyncio
from bleak import BleakScanner, BleakClient

# Define the UUIDs
SERVICE_UUID = "831c0e71-708a-4c5c-86ef-a71d64ad66ee"
CHARACTERISTIC_UUID = "831c0e71-708a-4c5c-86ef-a71d64ad66ee"

async def notification_handler(sender, data):
    """Handle notifications from the peripheral."""
    print(f"Notification from {sender}: {data.decode()}")  # Decode the data into a string

async def main():
    print("Scanning for peripherals...")
    devices = await BleakScanner.discover()

    # Find the target device
    target_device = None
    for device in devices:
        print(f"Found device: {device.name} [{device.address}]")
        if device.name == "Nicla BLE":  # Replace with your peripheral's advertised name
            target_device = device
            break

    if not target_device:
        print("Peripheral not found.")
        return

    print(f"Connecting to {target_device.name} [{target_device.address}]...")
    async with BleakClient(target_device.address) as client:
        print("Connected!")

        # Ensure the service and characteristic exist
        services = await client.get_services()
        print("Available services:")
        for service in services:
            print(service)

        # Subscribe to the characteristic notifications
        if CHARACTERISTIC_UUID in [char.uuid for char in services.get_service(SERVICE_UUID).characteristics]:
            print("Subscribing to notifications...")
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)

            print("Receiving notifications. Press Ctrl+C to exit.")
            while True:
                await asyncio.sleep(1)
        else:
            print("Characteristic not found!")

asyncio.run(main())
