from openai import OpenAI
import os
import sys
import json
import serial
from dotenv import load_dotenv
from datetime import date
import time
import bleak
from bleak import BleakScanner, BleakClient
import asyncio


device_address = "A8:61:0A:3E:66:14"
characteristic_uuid = "831c0e71-708a-4c5c-86ef-a71d64ad66ee"

async def scan_devices():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"found device {device.name}")

async def connect():
    async with BleakClient(device_address) as client:
        print(f"connected to {device_address}")

        value = await client.read_gatt_char(characteristic_uuid)

#asyncio.run(scan_devices())
asyncio.run(connect())



# Constants and setup
USB_PORT = "/dev/ttyACM0"
try:
    usb = serial.Serial(USB_PORT, 9600, timeout=2)
    time.sleep(2)
except:
    print("Couldn't find the Arduino, exiting...")
    exit()

load_dotenv()
client = OpenAI()
args = sys.argv
GPT_MODEL = "gpt-4o-mini"


# Define functions
def get_secret_code():
    return "twiddlevee!"

def turn():
    usb.write(b'turn')
    return "turned"

# Prepare messages and tools

while True:
    
    del args[0]
    today_date = date.today()

    prompt = ''.join(str(arg) + " " for arg in args)
    messages = [
        {"role": "system", "content": "You are a robot."},
        {"role": "user", "content": prompt},
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_secret_code",
                "description": "Gets the secret code",
            },
        },
        {
            "type": "function",
            "function": {
                "name": "turn",
                "description": "Turns the servo 180 degrees and then back.",
            },
        },
    ]

    # Generate completion
    completion = client.chat.completions.create(
        model=GPT_MODEL,
        messages=messages,
        tools=tools
    )

    response_message = completion.choices[0].message
    messages.append(response_message)
    
    # Debug: Check the response message
    #print("Response Message:", response_message)
    
    # Handle tool calls
    
    tool_calls = response_message.tool_calls
    if tool_calls:
        tool_call_id = tool_calls[0].id
        tool_function_name = tool_calls[0].function.name
        if tool_function_name == 'get_secret_code':
            results = get_secret_code()

            messages.append({
                "role":"tool",
                "tool_call_id":tool_call_id,
                "name": tool_function_name,
                "content":results
            })

            model_response_with_function_call = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            )
            print(model_response_with_function_call.choices[0].message.content)



        elif tool_function_name == 'turn':
            results = turn()

            messages.append({
                "role":"tool",
                "tool_call_id":tool_call_id,
                "name": tool_function_name,
                "content":results
            })


            model_response_with_function_call = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
            )
            print(model_response_with_function_call.choices[0].message.content)

    else:
        print(completion.choices[0].message.content)

    print("\n")
