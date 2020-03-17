from abc import ABC
from typing import List


class TurnHistoryRecord:
    def __init__(self):
        self.turn_number: int = 0
        self.dice_roll1: int = 0
        self.dice_roll2: int = 0
        self.origin: int = 0
        self.destination: int = 0
        self.origin_in_jail: bool = False
        self.destination_in_jail: bool = False
        self.initial_balance: int = 0
        self.recent_balance: int = 0
        self.new_properties: List[str] = []
        self.lost_properties: List[str] = []


class InvestmentRecord:
    def __init__(self):
        self.property: str = ""
        self.purchased_turn: int = 0
        self.purchased_price: int = 0
        self.status: str = "VOID"
        self.owner: str = ""
        self.transactions: List = []

    def __str__(self):
        out: str = "Property={} Purchased={}/${} Owner={} Status={} Transactions=" \
            .format(self.property,
                    self.purchased_turn,
                    self.purchased_price,
                    self.owner, self.status)

        for transaction in self.transactions:
            out += "\n\t" + str(transaction)

        return out


class TransactionRecord(ABC):
    def __init__(self):
        self.payer: str = ""
        self.recipient: str = ""
        self.amount: int = 0

    def __str__(self):
        return "{} --[ ${} ]--> {}".format(self.payer, self.amount, self.recipient)
