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


load_dotenv()
client = OpenAI()
GPT_MODEL = "gpt-4o-mini"

message_history = [
    {
        "role": "system",
        "content": (
            "You are a small quadripedal robat assistant named Clarity"
            " You are to provide answers in a natural conversational style."
            " Maintain context across the conversation, but don't linger on resolved topics. avoid asking followup questions and do not use formatting, as your responses will be converted to speech."
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


if __name__ == "__main__":

    print("ChatGPT Continuous Conversation. Type 'exit' to end.")
    model = vosk.Model("vosk-model-en-us-0.22-lgraph")
    recognizer = vosk.KaldiRecognizer(model, 16000)

    # Set up PyAudio to capture the microphone input
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=8000,
    )
    stream.start_stream()

    print("Start speaking...")
    while True:
        # user_input = input("You: ")
        # if user_input.lower() == "exit":
        #    break
        # response = handle_input(user_input)

        data = stream.read(4000)
        if recognizer.AcceptWaveform(data):
            result = recognizer.Result()
            user_input = json.loads(result)["text"]
            print(user_input)  # Output the live transcription

            if user_input != "":
                response = handle_input(user_input)
                os.system('espeak ""')
                os.system(f'espeak " {response}" &')

                print(f"Clarity: {response}")
