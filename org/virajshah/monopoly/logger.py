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


def generate_logstr(message):
    buffer = ""
    if include_date:
        today = datetime.date.today()
        buffer += "[ {}-{}-{}".format(today.year, today.month, today.day)
        if include_time:
            now = datetime.time()
            buffer += " | {}:{}:{} ] ".format(now.hour, now.minute, now.microsecond)
        else:
            buffer += " ] "
    elif include_time:
        now = datetime.time()
        buffer += "[ {}:{}:{} ] ".format(now.hour, now.minute, now.microsecond)
    return "{}\t{}".format(buffer, message)