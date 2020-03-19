from typing import List, IO

from org.virajshah.monopoly.html import DOMElement

printing_enabled: bool = False
include_date: bool = True
include_time: bool = True

logs: List["Log"] = []


class Log:
    def __init__(self, message: str, **kwargs):
        """
        Initialize a log wrapper.

        :param message: The message to be logged
        :param kwargs:
            type=str: Options: (default), transaction, player-update, bankrupted
        """
        self.message: str = message
        self.type: str = kwargs["type"] if "type" in kwargs else "default"

    def css(self) -> str:
        """
        Get the css of the log

        :return: The CSS for if the log is injected in HTML
        """

        fg: str = ""
        bg: str = "linear-gradient(to right, {}, {})"
        shadow: str = "0 0 50px 1px {}"

        if self.type == "transaction":
            fg = "black"
            bg = bg.format("#0ba360", "#3cba92")
            shadow = shadow.format("#0ba360")
        elif self.type == "player-update":
            fg = "black"
            bg = bg.format("#fa709a", "#fee140")
            shadow = shadow.format("orangered")
        elif self.type == "bankrupted":
            fg = "black"
            bg = bg.format("#eea2a2 0%, #bbc1bf 19%, #57c6e1 42%", "#b49fda 79%, #7ac5d8 100%")
            shadow = shadow.format("lightblue")
        else:  # default
            fg = "white"
            bg = bg.format("black", "rgb(50, 50, 50)")
            shadow = shadow.format("black")

        return 'color:{};background:{};box-shadow:{}'.format(fg, bg, shadow)

    def __str__(self):
        """
        :return: The logged message
        """
        return self.message


class Logger:
    @staticmethod
    def log(message: str, **kwargs) -> None:
        """
        Log a message to the list of logs

        :param message: The message to append
        :param kwargs:
            type=...: The type of log being appended
        :return: None
        """
        if printing_enabled:
            print(message)
        logs.append(Log(message, **kwargs))

    @staticmethod
    def save(filename: str) -> None:
        """
        Save the logs to a file.

        :param filename: The file to save the logs to
            Note: *.html will generate an html doc for the logs
        :return: None
        """
        ext: str = filename.split(".")[-1] if "." in filename else "txt"
        buffer: IO = open(filename, "w")
        if ext in ["txt", "log"]:
            text: str = ""
            for log in logs:
                text += str(log) + "\n"
            buffer.write(text)
            buffer.close()
        elif ext in ["html", "htm"]:
            logs_html_list: List[DOMElement] = []

            for log in logs:
                logs_html_list.append(DOMElement("div", classname="log", style=log.css(), children=[log.message]))

            page: DOMElement = DOMElement("html", lang="en-US", children=[
                DOMElement("head", children=[
                    DOMElement("meta", charset="utf-8"),
                    DOMElement("title", children=["MonopolySimPy Log"]),
                    DOMElement("style", type="text/css", children=["""
                        .loglist {
                            padding-left: 10vw;
                            padding-right: 10vw;
                            padding-top: 10vh;
                            padding-bottom: 10vh;
                        }
                        
                        .log {
                            padding: 25px;
                            font-family: menlo, monospace;
                            margin-bottom: 50px;
                        }
                        
                        pre {
                            overflow-x: auto;
                            white-space: pre-wrap;
                            white-space: -moz-pre-wrap;
                            white-space: -pre-wrap;
                            white-space: -o-pre-wrap;
                            word-wrap: break-word;
                        }
                    """])
                ]),
                DOMElement("body", children=[
                    DOMElement("pre", classname="loglist", children=logs_html_list)
                ])
            ])

            buffer.write(str(page))
            buffer.close()
            print("Logs saved to {}".format(filename))
