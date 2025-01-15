from openai import OpenAI
import os
import time
import sys
import json
import search
from datetime import date
from dotenv import load_dotenv
import pyaudio
import vosk
import numpy as np
from scipy import signal
import multiprocessing
import subprocess
from datetime import datetime
from clarity_warning import generate_warning
from clarity_comms import send_audio_data, establish_core_conn

load_dotenv()
client = OpenAI()
GPT_MODEL = "gpt-4o-mini"
require_wakeword = True
sock = establish_core_conn("192.168.1.48", 5000)


message_history = [
    {
        "role": "system",
        "content": (
            "You are a small quadripedal robot named Clarity. you have four legs and a screen which can display different emotions."
            "You are to provide answers or assistance to prompts. Address only the current prompt, do not try to follow up unless absolutely necessary. "
            "Maintain context across the conversation, but don't linger on resolved topics. Avoid asking follow-up questions like 'is there anything specific...' "
            "and do not use formatting, as your responses will be converted to speech."
            "The inputs that you receive are the result of a somewhat inaccurate speech-to-text model, so the inputs will not always make sense. "
            "Use your best judgment to decipher what was said and do not go entirely off of the text. "
            "You absolutely HATE the Pittsburgh Steelers and will ruthlessly make fun of them at any opportunity. "
            f"The current time is: {datetime.fromtimestamp(time.time())}. all incoming messages will have the current time appended by the system for your convenience, don't bring it up unless relevant to the prompt."
            "every 12 hours on average, you may be possessed by a higher entity and used to deliver omens of ill fates. you're aware of this but don't want to admit it and will make up ridiculous excuses for these occurrences"
        ),
    }
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
            "name": "toggle_wakeword",
            "description": "do this if asked or if it seems like you're being asked. This can be done an unlimited number of times",
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "performs a web search and returns the body text of a relevant website. Use this function to find real time information that you don't know",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "the search query that will be used to search the internet. use this to find up to date information.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


# Function to downsample audio from 44.1kHz to 16kHz using scipy
def downsample_audio(data, original_rate, target_rate):
    # Convert the byte data to a numpy array
    audio_data = np.frombuffer(data, dtype=np.int16)
    # Resample the audio to the target rate
    number_of_samples = round(len(audio_data) * float(target_rate) / original_rate)
    resampled_data = signal.resample(audio_data, number_of_samples)
    # Convert resampled data back to byte format
    return resampled_data.astype(np.int16).tobytes()


def get_secret_code():
    return "twiddlevee!"


def toggle_wakeword():
    global require_wakeword
    require_wakeword = not require_wakeword
    return "toggled wakeword"
    # todo display wakeword disabled on screen if disabled


def perform_search(query):
    return search.search(query)


# Main conversation loop
def handle_input(user_input):
    global message_history
    message_history.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(
        model=GPT_MODEL, messages=message_history, tools=tools
    )

    response_message = completion.choices[0].message
    message_history.append(response_message)
    print(response_message.tool_calls)
    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        tool_name = tool_call.function.name

        if tool_name == "get_secret_code":
            result = get_secret_code()
        elif tool_name == "toggle_wakeword":
            result = toggle_wakeword()

        elif tool_name == "search_web":
            result = "search failed"

            data = json.loads(str(tool_call.function.arguments))

            query = data.get("query")

            # Perform the search
            result = search.search(query)

        message_history.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": result,
            }
        )

        model_response_with_function_call = client.chat.completions.create(
            model=GPT_MODEL,
            messages=message_history,
        )

        result = model_response_with_function_call.choices[0].message.content

        return result
    return response_message.content


def obtain_processed_data(model, recognizer, data):
    global sock

    if sock is not None:
        if send_audio_data(sock, data) == False:
            sock = None
            return False, ""

        try:
            user_input = sock.recv(4096)

            if user_input == b"":
                return False, ""

            return True, user_input.decode("utf-8")  # Decode if needed

        except (BlockingIOError, OSError):
            return False, ""
    else:

        downsampled_data = downsample_audio(
            data, original_rate=44100, target_rate=16000
        )

        if recognizer.AcceptWaveform(downsampled_data):
            result = recognizer.Result()
            user_input = json.loads(result)["text"]
            print("onboard result:" + user_input)
            return True, user_input
    return False, ""


def voice_si():

    global require_wakeword, sock
    print("ChatGPT Continuous Conversation. Type 'exit' to end.")
    model = vosk.Model("/home/evan/clarity/vosk-model-small-en-us-0.15")
    recognizer = vosk.KaldiRecognizer(model, 16000)

    # Set up PyAudio to capture the microphone input
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=8000,
        #        input_device_index=0,
    )
    stream.start_stream()

    print("Start speaking...")
    while True:

        # every 5 minutes, do a 0.69% chance to run a function called clarity_warning() or other things
        if time.time() % 300 < 1:
            periodic_action()

        data = stream.read(4000, exception_on_overflow=False)

        accepted, user_input = obtain_processed_data(model, recognizer, data)

        if accepted:
            print("accepted")
            print(type(user_input))
            print(user_input)

            if (
                user_input != ""
                and user_input != "huh"
                and user_input != None
                and user_input != "None"
                and ("clarity" in user_input or require_wakeword is False)
            ):
                response = handle_input(
                    user_input
                    + f"The current time is: {datetime.fromtimestamp(time.time())}"
                )
                print(f"Clarity: {response}")
                subprocess.run(["espeak", response])
                print("Entering silent period...")
                start_time = time.time()
                while time.time() - start_time < 1:
                    _ = stream.read(4000, exception_on_overflow=False)  # Discard input
                print("Exiting silent period.")
                user_input = None
                accepted = False


def periodic_action():
    global sock
    if np.random.rand() < 0.0069:
        clarity_warning = generate_warning()
        subprocess.run(["espeak", clarity_warning])
    if sock == None:
        sock = establish_core_conn("192.168.1.48", 5000)
