from typing import Union, List

from org.virajshah.monopoly.records import InvestmentRecord, TransactionRecord


class InvestmentTracker:
    def __init__(self):
        self.ledger: List[InvestmentRecord] = []

    def track_property(self, prop_name: str, owner: str, turn: int, price: int):
        record: InvestmentRecord = InvestmentRecord()
        record.property = prop_name
        record.owner = owner
        record.purchased_turn = turn
        record.purchased_price = price
        record.status = "ACTIVE"
        self.ledger.append(record)

    def find_active(self, prop_name: str) -> Union[InvestmentRecord, None]:
        for record in self.ledger:
            if record.property == prop_name and record.status == "ACTIVE":
                return record
        return None

    def rent_collected(self, prop_name, payer, amount):
        record: InvestmentRecord = self.find_active(prop_name)
        if record is not None:
            transaction: TransactionRecord = TransactionRecord()
            transaction.payer = payer
            transaction.recipient = record.owner
            transaction.amount = amount
            record.transactions.append(transaction)
        else:
            raise IndexError("No active record for '{}' could be found".format(prop_name))
