from org.virajshah.monopoly import tiles
from org.virajshah.monopoly.banker import TradeManager
from org.virajshah.monopoly.logger import Logger, InfoLog, RentTransactionLog
from org.virajshah.monopoly.records import TurnHistoryRecord
from org.virajshah.monopoly.tiles import TileAttribute
from org.virajshah.monopoly.core import Player
from random import randrange

JAIL_INDEX = 10

logger = Logger()


class MonopolyGame:
    # Fields: Tile[] board, Player[] players, Player[] bankrupted_players, int curr_player
    def __init__(self):
        self.board = tiles.build_board()  # Tile[]
        self.players = []
        self.bankrupted_players = []
        self.curr_player = -1

    def add_player(self, player: Player):
        if isinstance(player, Player):
            self.players.append(player)
            player.game = self

    def run_next_turn(self):
        if len(self.players) == 0:
            logger.log(InfoLog("There are no remaining players"))
            return

        self.curr_player += 1

        if self.curr_player >= len(self.players):
            self.curr_player = 0

        player = self.players[self.curr_player]
        turn = TurnHistoryRecord()

        player.turn_history.append(turn)
        turn.turn_number = len(player.turn_history)
        turn.dice_roll1 = randrange(1, 7)
        turn.dice_roll2 = randrange(1, 7)
        turn.origin = player.position
        turn.origin_in_jail = player.prisoner
        turn.initial_balance = player.balance

        logger.log(
            InfoLog("It is {}'s turn #{}. Starting at {}.".format(player.name, turn.turn_number, player.position)))
        logger.log(InfoLog(
            "Dice Roll: {} and {} = {}".format(turn.dice_roll1, turn.dice_roll2, turn.dice_roll1 + turn.dice_roll2)))

        if player.prisoner and turn.dice_roll1 == turn.dice_roll2:
            logger.log(InfoLog(
                "{} is in jail, but rolled doubles ({}), and is now out of jail.".format(player.name, turn.dice_roll1)))
        elif player.prisoner:
            logger.log(InfoLog(player.name + " is still stuck in jail (and didn't roll doubles)."))
            return

        player.position += turn.dice_roll1 + turn.dice_roll2
        if player.position > 39:
            player.position = player.position - 40

        logger.log(InfoLog("{} moved to {}".format(player.name, self.board[player.position].name)))

        if TileAttribute.GO_TO_JAIL in self.board[player.position].attributes:
            player.position = JAIL_INDEX
            turn.destination_in_jail = True
            logger.log(InfoLog(player.name + " is now in jail."))
            return

        turn.destination_in_jail = False
        turn.destination = player.position

        if TileAttribute.PROPERTY in self.board[player.position].attributes:
            prop = self.board[player.position]  # PropertyTile

            if not prop.owner and player.balance > prop.price:
                prop.purchase(player)
                turn.new_properties.append(player.position)
                logger.log(InfoLog("{} purchased {} for ${}".format(player.name, prop.name, prop.price)))
            elif prop.owner and prop.owner != player:
                rent_due = prop.rent(roll=(turn.dice_roll1 + turn.dice_roll2))
                player.send_money(rent_due, prop.owner)
                logger.log(RentTransactionLog(player, prop.owner, rent_due, prop))

        TradeManager.run_best_trade(player)
        turn.recent_balance = player.balance

        if player.balance < 0:
            self.bankrupted_players.append(player)
            self.players.remove(player)
            logger.log(InfoLog("{} is now bankrupt (${}). Removing from the game.".format(player.name, player.balance)))

        # TODO: Log turn history record

    # TODO: Write method for logAllPlayerUpdates()


class Player:
    # Fields: str name, int balance, int position, TurnHistoryRecord turn_history, PropertyTile[] properties,
    #         bool prisoner
    def __init__(self, name: str):
        self.name = name  # str
        self.balance = 1500
        self.position = 0
        self.turn_history = []
        self.properties = []
        self.prisoner = False
        self.game = None  # Game is assigned by MonopolyGame

    def send_money(self, amount: int, other_player: Player):
        self.add_money(-amount)
        other_player.add_money(amount)

    def add_money(self, amount: int):
        self.balance += amount
