from typing import List

from org.virajshah.monopoly.core import MonopolyGame
from org.virajshah.monopoly.records import InvestmentRecord
from org.virajshah.monopoly.tracker import InvestmentTracker
from org.virajshah.monopoly.logger import Logger, logs as logger_logs

if __name__ == "__main__":
    game: MonopolyGame = MonopolyGame(players=["Player 1", "Player 2", "Player 3", "Player 4"])

    while len(game.players) > 1:
        game.run_next_turn()

    Logger.save("/tmp/ROI_logs.html")
    investments: InvestmentTracker = game.investment_tracker
    all_records: List[InvestmentRecord] = game.investment_tracker.ledger
    active_record: List[InvestmentRecord] = [record for record in all_records if record.status == "ACTIVE"]
    logger_logs.clear()
    for record in active_record:
        Logger.log(str(record))
    Logger.save("/tmp/ROI_simulation.html")
