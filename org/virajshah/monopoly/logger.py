import datetime
from typing import List, IO

printing_enabled: bool = True
include_date: bool = True
include_time: bool = True
logs: List[str] = []


class Logger:
    @staticmethod
    def log(message: str):
        if printing_enabled:
            print(message)
        logs.append(message)

    @staticmethod
    def save(filename: str):
        buffer: IO = open(filename, "w")
        text: str = ""
        for log in logs:
            text += str(log) + "\n"
        buffer.write(text)
        buffer.close()
