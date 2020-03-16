printing_enabled = False
logs = []


class Logger:
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        if printing_enabled:
            print(message)
        self.logs.append(message)

    def save(self, filename: str):
        buffer = open(filename, "w")
        text = ""
        for log in self.logs:
            text += str(log) + "\n"
        buffer.write(text)
        buffer.close()

    def __int__(self):
        return len(self.logs)

    def __str__(self):
        return "Logger({})".format(__name__)
