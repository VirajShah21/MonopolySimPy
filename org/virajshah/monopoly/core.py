from org.virajshah.monopoly import tiles
from org.virajshah.monopoly.banker import TradeManager
from org.virajshah.monopoly.records import TurnHistoryRecord
from org.virajshah.monopoly.tiles import TileAttribute
from random import randrange

JAIL_INDEX = 10


class MonopolyGame:
    def __init__(self):
        self.board = tiles.build_board()  # Tile[]
        self.players = []
        self.bankrupted_players = []
        self.curr_player = -1

    def add_player(self, player):
        if isinstance(player, Player):
            self.players.append(player)
            player.game = self

    def run_next_turn(self):
        if len(self.players) == 0:
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
        turn.origin_in_jail = player.is_prisoner
        turn.initial_balance = player.balance

        if player.is_prisoner and turn.dice_roll1 == turn.dice_roll2:
            print("Replace this with a log")
        else:
            print("Replace this with a log")
            return

        player.position += turn.dice_roll1 + turn.dice_roll2
        if player.position > 39:
            player.position = player.position - 40

        if TileAttribute.GO_TO_JAIL in self.board[player.position].attributes:
            player.position = JAIL_INDEX
            turn.destination_in_jail = True
            return

        turn.destination_in_jail = False
        turn.destination = player.position

        if TileAttribute.PROPERTY in self.board[player.position].attributes:
            prop = self.board[player.position]  # PropertyTile

            if prop.is_owned() and player.balance > prop.price:
                prop.purchase(player)
                turn.new_properties.append(player.position)
            elif prop.is_owned() and prop.owner != player:
                rent_due = prop.getRent(turn.dice_roll1 + turn.dice_roll2)
                player.send_money(rent_due, prop.owner)

        TradeManager.run_best_trade(player)
        turn.recent_balance = player.balance

        if player.balance < 0:
            self.bankrupted_players.append(player)
            self.players.remove(player)

    # TODO: Write method for logAllPlayerUpdates()


class Player:
    def __init__(self, name):
        self.name = name  # str
        self.balance = 1500
        self.position = 0
        self.turn_history = []
        self.properties = []
        self.prisoner = False

    def send_money(self, amount, other):
        self.add_money(-amount)
        other.add_money(amount)

    def add_money(self, amount):
        self.balance += amount
