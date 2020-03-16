import datetime

printing_enabled = True
include_date = True
include_time = True
logs = []


class Logger:
    @staticmethod
    def log(message: str):
        to_log = generate_logstr(message)
        if printing_enabled:
            print(to_log)
        logs.append(to_log)

    @staticmethod
    def save(filename: str):
        buffer = open(filename, "w")
        text = ""
        for log in logs:
            text += str(log) + "\n"
        buffer.write(text)
        buffer.close()


def generate_logstr(message: str) -> str:
    buffer = ""
    if include_date:
        today = datetime.date.today()
        buffer += "[ {}-{}-{}".format(str(today.year).zfill(4), str(today.month).zfill(2), str(today.day).zfill(2))
        if include_time:
            now = datetime.datetime.now()
            buffer += " | {}:{}:{} ] ".format(str(now.hour).zfill(2), str(now.minute).zfill(2), now.microsecond)
        else:
            buffer += " ] "
    elif include_time:
        now = datetime.datetime.now()
        buffer += "[ {}:{}:{} ] ".format(str(now.hour).zfill(2), str(now.minute).zfill(2), now.microsecond)
    return "{}\t{}".format(buffer, message)
