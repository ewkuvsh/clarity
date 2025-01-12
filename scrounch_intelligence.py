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

load_dotenv()
client = OpenAI()
GPT_MODEL = "gpt-4o-mini"

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

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0]
        tool_name = tool_call.function.name

        if tool_name == "get_secret_code":
            result = get_secret_code()
        elif tool_name == "search_web":
            results = "search failed"

            data = json.loads(str(tool_call.function.arguments))

            query = data.get("query")

            # Perform the search
            results = search.search(query)

            message_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": results,
                }
            )

            model_response_with_function_call = client.chat.completions.create(
                model=GPT_MODEL,
                messages=message_history,
            )

            result = model_response_with_function_call.choices[0].message.content

        return result
    return response_message.content


def voice_si():

    print("ChatGPT Continuous Conversation. Type 'exit' to end.")
    model = vosk.Model("vosk-model-small-en-us-0.15")
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

        # every 5 minutes, do a 0.69% chance to run a function called clarity_warning()
        if time.time() % 300 < 1:
            periodic_action()

        data = stream.read(4000, exception_on_overflow=False)
        downsampled_data = downsample_audio(
            data, original_rate=44100, target_rate=16000
        )

        if recognizer.AcceptWaveform(downsampled_data):
            result = recognizer.Result()
            user_input = json.loads(result)["text"]
            print(user_input)

            if user_input != "" and user_input != "huh" and "clarity" in user_input:
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


def periodic_action():
    if np.random.rand() < 0.0069:
        clarity_warning = generate_warning()
        subprocess.run(["espeak", clarity_warning])
        
    else:
        # system message: do you want to do something?
        print("does you want to do smth")



