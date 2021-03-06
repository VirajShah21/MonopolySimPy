from typing import Union, List, IO

from org.virajshah.monopoly.html import DOMElement
from org.virajshah.monopoly.records import InvestmentRecord, TransactionRecord


class InvestmentTracker:
    def __init__(self):
        self.ledger: List[InvestmentRecord] = []

    def track_property(self, prop_name: str, owner: str, turn: int, price: int) -> None:
        """
        Add a new InvestmentRecord for a property to the ledger

        :param prop_name: The name of the property
        :param owner: The owner of the property
        :param turn: The turn number (in the game)
        :param price: The purchase price of the property
        :return: None
        """

        record: InvestmentRecord = InvestmentRecord()
        record.property = prop_name
        record.owner = owner
        record.purchased_turn = turn
        record.purchased_price = price
        record.status = "ACTIVE"

        active_record: InvestmentRecord = self.find_active(prop_name)
        while active_record is not None:
            active_record.status = "INACTIVE"
            active_record = self.find_active(prop_name)

        self.ledger.append(record)

    def find_active(self, prop_name: str) -> Union[InvestmentRecord, None]:
        """
        Find an active InvestmentRecord based on the property name
        :param prop_name: The property name to query
        :return: An InvestmentRecord containing the most up-to-date
            information about a tracked property.
            **RETURNS None if no property could be found**
        """
        for record in self.ledger:
            if record.property == prop_name and record.status == "ACTIVE":
                return record
        return None

    def rent_collected(self, prop_name, payer, amount) -> None:
        """
        Add a note to the record that a player has collected rent on a property

        :param prop_name: The name of the property
        :param payer: The individual paying rent
        :param amount: The amount of rent due
        :return: None
        """

        record: InvestmentRecord = self.find_active(prop_name)
        if record is not None:
            transaction: TransactionRecord = TransactionRecord()
            transaction.payer = payer
            transaction.recipient = record.owner
            transaction.amount = amount
            record.transactions.append(transaction)
        else:
            raise IndexError("No active record for '{}' could be found".format(prop_name))

    def generate_html_table(self, filename: str) -> None:
        """
        Write all the transactions to an HTML table.

        :param filename: The output destination for the HTML file
        :return: None
        """
        table = DOMElement("table", border="1")
        table.append_child(DOMElement("thead", children=[
            DOMElement("th", children=["Property"]),
            DOMElement("th", children=["Owner"]),
            DOMElement("th", children=["Turn Purchased"]),
            DOMElement("th", children=["Initial Investment"]),
            DOMElement("th", children=["ROI"]),
            DOMElement("th", children=["Status"])
        ]))

        for record in self.ledger:
            tr: DOMElement = DOMElement("tr")
            tr.append_child(DOMElement("td", children=[record.property]))
            tr.append_child(DOMElement("td", children=[record.owner]))
            tr.append_child(DOMElement("td", children=[record.purchased_turn]))
            tr.append_child(DOMElement("td", children=[record.purchased_price]))
            tr.append_child(DOMElement("td", children=[str(
                sum([transaction.amount for transaction in record.transactions]) - record.purchased_price
            )]))
            tr.append_child(DOMElement("td", children=[
                DOMElement("b", children=["ACTIVE"]) if record.status == "ACTIVE" else record.status
            ]))
            table.append_child(tr)

        document = DOMElement("html", lang="en-US", children=[
            DOMElement("head", children=[
                DOMElement("meta", charset="UTF-8", autoclose=True),
                DOMElement("title", children=["Investment Tracker"])
            ]),
            DOMElement("body", children=[
                table
            ])
        ])

        fp: IO = open(filename, "w")
        fp.write("<!DOCTYPE html>" + str(document))
        fp.close()

    def __str__(self):
        """
        :return: Each record on a new line
        """
        out: str = ""
        for record in self.ledger:
            out += str(record) + "\n"
        return out
