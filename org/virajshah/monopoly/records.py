from abc import ABC


class TurnHistoryRecord:
    def __init__(self):
        self.turn_number = 0
        self.dice_roll1 = 0
        self.dice_roll2 = 0
        self.origin = 0
        self.destination = 0
        self.origin_in_jail = False
        self.destination_in_jail = False
        self.initial_balance = 0
        self.recent_balance = 0
        self.new_properties = []
        self.lost_properties = []


class InvestmentRecord:
    def __init__(self):
        self.property = None
        self.purchased_turn = 0
        self.purchased_price = 0
        self.status = "VOID"
        self.owner = None
        self.transactions = []


class TransactionRecord(ABC):
    def __init__(self):
        self.payer = None
        self.recipient = None
        self.amount = 0
