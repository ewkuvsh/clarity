from enum import Enum


class Data(Enum):
    STRING = 1
    SOUND = 2
    IMAGE = 3


class Destination(Enum):
    MAIN = 1
    CORE = 2
    LOOK = 3
    VOICE = 4


class Source(Enum):
    MAIN = 1
    CORE = 2
    LOOK = 3
    VOICE = 4


class Message:
    def __init__(self, src, dest, data):
        self.src = src
        self.data = data
        self.data = data

    def __repr__(self):
        return f"Message(src={self.src.name}, dest={self.dest.name}, data={self.data})"
