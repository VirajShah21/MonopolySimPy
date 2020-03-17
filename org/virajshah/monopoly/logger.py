import datetime
from typing import List, IO

printing_enabled: bool = True
include_date: bool = True
include_time: bool = True
logs: List[str] = []


class Logger:
    @staticmethod
    def log(message: str):
        to_log: str = generate_logstr(message)
        if printing_enabled:
            print(to_log)
        logs.append(to_log)

    @staticmethod
    def save(filename: str):
        buffer: IO = open(filename, "w")
        text: str = ""
        for log in logs:
            text += str(log) + "\n"
        buffer.write(text)
        buffer.close()


def generate_logstr(message: str) -> str:
    buffer: str = ""
    if include_date:
        today: datetime.date = datetime.date.today()
        buffer += "[ {}-{}-{}".format(str(today.year).zfill(4), str(today.month).zfill(2), str(today.day).zfill(2))
        if include_time:
            now: datetime.datetime = datetime.datetime.now()
            buffer += " | {}:{}:{} ] ".format(str(now.hour).zfill(2), str(now.minute).zfill(2), now.microsecond)
        else:
            buffer += " ] "
    elif include_time:
        now: datetime.datetime = datetime.datetime.now()
        buffer += "[ {}:{}:{} ] ".format(str(now.hour).zfill(2), str(now.minute).zfill(2), now.microsecond)
    return "{}\t{}".format(buffer, message)
