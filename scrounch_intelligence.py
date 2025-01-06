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

load_dotenv()
client = OpenAI()
GPT_MODEL = "gpt-4o-mini"

message_history = [
    {
        "role": "system",
        "content": (
            "You are a small quadripedal robat assistant named Clarity"
            " You are to provide answers in a natural conversational style."
            " Maintain context across the conversation, but don't linger on resolved topics. avoid asking followup questions (like is there anything specific...) and do not use formatting, as your responses will be converted to speech."
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
        input_device_index=0,
    )
    stream.start_stream()

    print("Start speaking...")
    while True:
        # user_input = input("You: ")
        # if user_input.lower() == "exit":
        #    break
        # response = handle_input(user_input)

        data = stream.read(4000, exception_on_overflow=False)
        downsampled_data = downsample_audio(
            data, original_rate=44100, target_rate=16000
        )

        if recognizer.AcceptWaveform(downsampled_data):
            result = recognizer.Result()
            user_input = json.loads(result)["text"]
            print(user_input)  # Output the live transcription

            if user_input != "":
                response = handle_input(user_input)
                os.system('espeak ""')
                os.system(f'espeak " {response}" &')

                print(f"Clarity: {response}")
