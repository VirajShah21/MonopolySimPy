from typing import List, IO

from org.virajshah.monopoly.html import DOMElement
import os

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

        fg: str
        bg: str = "linear-gradient(to right, {}, {})"
        shadow: str = "0 0 50px 1px {}"

        if self.type == "transaction":
            fg = "black"
            bg = bg.format("#0ba360", "#3cba92")
            shadow = shadow.format("#0ba360")
        elif self.type == "player-update":
            fg = "black"
            bg = bg.format("#667eea", "#764ba2")
            shadow = shadow.format("#6f30af")
        elif self.type == "bankrupted":
            fg = "black"
            bg = bg.format("#eea2a2 0%, #bbc1bf 19%, #57c6e1 42%", "#b49fda 79%, #7ac5d8 100%")
            shadow = shadow.format("lightblue")
        elif self.type == "trade":
            fg = "black"
            bg = bg.format("#2575fc", "#66a6ff")
            shadow = shadow.format("#66a6ff")
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
    def enable_printing() -> None:
        """
        Enables printing
        :return: None
        """
        global printing_enabled
        printing_enabled = True

    @staticmethod
    def save(filename: str) -> None:
        """
        Save the logs to a file.

        :param filename: The file to save the logs to
            Note: *.html will generate an html doc for the logs
        :return: None
        """
        print("Saving {} logs".format(len(logs)))
        ext: str = filename.split(".")[-1] if "." in filename else "txt"
        buffer: IO = open(filename, "w")
        if ext in ["txt", "log"]:
            text: str = ""
            for log in logs:
                text += str(log) + "\n"
            buffer.write(text)
        elif ext in ["html", "htm"]:
            game_board_fp: IO = open(os.path.dirname(os.path.realpath(__file__)) + "/html_components/game-board.html",
                                     "r")
            game_board_html: str = game_board_fp.read()
            game_board_fp.close()
            del game_board_fp

            logs_html_list: List[DOMElement] = []
            log_num = 1
            for log in logs:
                logs_html_list.append(
                    DOMElement("div", id="log-{}".format(log_num), children=[
                        DOMElement("span", style="padding-left:2em", children=[str(log_num)]),
                        DOMElement("pre", classname="log", style=log.css(), children=[log.message])]))
                log_num += 1

            page: DOMElement = DOMElement("html", lang="en-US", children=[
                DOMElement("head", children=[
                    DOMElement("meta", charset="utf-8"),
                    DOMElement("title", children=["MonopolySimPy Log"]),
                    DOMElement("style", type="text/css", children=["""                   
                    pre {
                        overflow-x: auto;
                        white-space: pre-wrap;
                        white-space: -moz-pre-wrap;
                        white-space: -pre-wrap;
                        white-space: -o-pre-wrap;
                        word-wrap: break-word;
                    }
                    
                    .log-list {
                        padding-left: 10vw;
                        padding-right: 10vw;
                        padding-top: 10vh;
                        padding-bottom: 10vh;
                    }
                    
                    .log {
                        padding: 25px;
                        font-family: menlo, monospace;
                        margin-bottom: 50px;
                        border-radius: 15px;
                    }
                    
                    #menubar {
                        width: 100%;
                        position: fixed;
                        top: 0;
                        box-sizing: border-box;
                        padding: 1em;
                        background-color: rgba(255, 255, 255, 0.5);
                        -webkit-backdrop-filter: blur(20px);
                        backdrop-filter: blur(20px);                        
                    }
                    
                    #menubar a {
                        color: gray;
                        text-decoration: none;
                        padding: 1em;
                        box-sizing: border-box;
                        font-family: "Avenir Next", "Helvetica Neue", "Arial"
                    }
                    
                    #game-board-wrapper {
                        width:100vw;
                        height:100vh;
                        position:fixed;
                        z-index:100;
                        text-align: center;
                        -webkit-backdrop-filter: blur(20px);
                        backdrop-filter: blur(20px);
                    }
                """])
                ]),
                DOMElement("body", children=[
                    DOMElement("div", id="menubar", children=[
                        DOMElement("a", children=["#"],
                                   onclick="window.location = '#log-' + prompt('Jump to log #:');"),
                        DOMElement("a", children=["Top"], href="#log-1"),
                        DOMElement("a", children=["Bottom"], href="#log-{}".format(len(logs))),
                        DOMElement("a", children=["Game Board"],
                                   onclick="document.getElementById('game-board-wrapper').hidden=false")
                    ]),
                    DOMElement("div",
                               id="game-board-wrapper",
                               children=[
                                   game_board_html,
                                   DOMElement("button", children=["Close"],
                                              onclick="document.getElementById('game-board-wrapper').hidden=true")
                               ], hidden="false"),
                    DOMElement("pre", classname="log-list", children=logs_html_list)
                ])
            ])
            buffer.write(str(page))
        buffer.close()
        print("Logs saved to {}".format(filename))
