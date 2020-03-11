from abc import ABC

log_configuration = {
    "format": "text",
    "no_write": [],
    "no_print": []
}


class Logger:
    def __init__(self):
        self.logs = []

    def log(self, data):
        print(data.message)
        self.logs.append(data)

    def save(self, filename):
        if log_configuration["format"].lower() == "text":
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


class Log(ABC):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class InfoLog(Log):
    def __init__(self, message):
        super().__init__(message)


class TransactionLog(Log):
    def __init__(self, sender, receiver, amount):
        super().__init__("Transaction: {} -- ${} --> {}".format(sender, amount, receiver))
        self.sender = sender
        self.receiver = receiver
        self.amount = amount


class RentTransactionLog(TransactionLog):
    def __init__(self, sender, receiver, amount, prop):
        super().__init__(sender, receiver, amount)
        self.property = prop
