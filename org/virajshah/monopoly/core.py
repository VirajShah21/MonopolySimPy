from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Union, Dict, cast

from org.virajshah.monopoly.logger import Logger
from org.virajshah.monopoly.records import TurnHistoryRecord
from random import randrange

from org.virajshah.monopoly.tracker import InvestmentTracker

JAIL_INDEX = 1


class MonopolyGame:
    # Fields: Tile[] board, Player[] players, Player[] bankrupted_players, int curr_player
    def __init__(self):
        self.board: List[Tile] = build_board()  # Tile[]
        self.players: List[Player] = []
        self.bankrupted_players: List[Player] = []
        self.curr_player: int = -1
        self.turn_number: int = 0
        self.investment_tracker: InvestmentTracker = InvestmentTracker()

    def add_player(self, player: "Player"):
        self.players.append(player)

    def run_next_turn(self):
        if len(self.players) == 0:
            Logger.log("There are no remaining players")
            return

        self.curr_player += 1

        if self.curr_player >= len(self.players):
            self.curr_player = 0

        player: Player = self.players[self.curr_player]
        turn: TurnHistoryRecord = TurnHistoryRecord()
        self.turn_number = 0

        player.turn_history.append(turn)
        turn.turn_number = len(player.turn_history)
        turn.dice_roll1 = randrange(1, 7)
        turn.dice_roll2 = randrange(1, 7)
        turn.origin = player.position
        turn.origin_in_jail = player.prisoner
        turn.initial_balance = player.balance

        Logger.log(
            "It is {}'s turn #{}. Starting at {}.".format(player.name, turn.turn_number, player.position))
        Logger.log(
            "Dice Roll: {} and {} = {}".format(turn.dice_roll1, turn.dice_roll2, turn.dice_roll1 + turn.dice_roll2))

        if player.prisoner and turn.dice_roll1 == turn.dice_roll2:
            Logger.log(
                "{} is in jail, but rolled doubles ({}), and is now out of jail.".format(player.name, turn.dice_roll1))
        elif player.prisoner:
            Logger.log(player.name + " is still stuck in jail (and didn't roll doubles).")
            return

        player.position += turn.dice_roll1 + turn.dice_roll2
        if player.position > 39:
            player.position = player.position - 40

        Logger.log("{} moved to {}".format(player.name, self.board[player.position].name))

        if TileAttribute.GO_TO_JAIL in self.board[player.position].attributes:
            player.position = JAIL_INDEX
            turn.destination_in_jail = True
            Logger.log(player.name + " is now in jail.")
            return

        turn.destination_in_jail = False
        turn.destination = player.position

        if TileAttribute.PROPERTY in self.board[player.position].attributes:
            prop: Property = cast(Property, self.board[player.position])

            if not prop.owner and player.balance > prop.price:
                prop.purchase(player)
                turn.new_properties.append(prop.name)
                self.investment_tracker.track_property(prop.name, prop.owner.name, self.turn_number, prop.price)
                Logger.log("{} purchased {} for ${}".format(player.name, prop.name, prop.price))
            elif prop.owner and prop.owner != player:
                rent_due = prop.rent(roll=(turn.dice_roll1 + turn.dice_roll2))
                player.send_money(rent_due, prop.owner)
                Logger.log("{} payed {} ${} for rent on {}".format(player, prop.owner, rent_due, prop))

        TradeManager.run_best_trade(player)
        turn.recent_balance = player.balance

        if player.balance < 0:
            self.bankrupted_players.append(player)
            self.players.remove(player)
            Logger.log("{} is now bankrupt (${}). Removing from the game.".format(player.name, player.balance))

        player.turn_history.append(turn)
        self.log_all_player_updates()

    def log_all_player_updates(self):
        for p in self.players:
            Logger.log("\t {} has ${} and {}".format(p.name, p.balance, [str(prop) for prop in p.properties]))


class Player:
    # Fields: str name, int balance, int position, TurnHistoryRecord turn_history, PropertyTile[] properties,
    #         bool prisoner
    def __init__(self, name: str, game: MonopolyGame):
        self.name: str = name
        self.balance: int = 1500
        self.position: int = 0
        self.turn_history: List[TurnHistoryRecord] = []
        self.properties: List[Property] = []
        self.prisoner: bool = False
        self.game: MonopolyGame = game  # Game is assigned by MonopolyGame

    def send_money(self, amount: int, other_player: "Player"):
        self.add_money(-amount)
        other_player.add_money(amount)

    def add_money(self, amount: int):
        self.balance += amount

    def __str__(self):
        return self.name


class TileAttribute(Enum):
    GO = 1
    TAX = 2
    PROPERTY = 3
    CHEST = 4
    CHANCE = 5
    SET1 = 6
    SET2 = 7
    SET3 = 8
    SET4 = 9
    SET5 = 10
    SET6 = 11
    SET7 = 12
    SET8 = 13
    JAIL = 14
    GO_TO_JAIL = 15
    RAILROAD = 16
    UTILITY = 17
    FREE_PARKING = 18
    COLORED_PROPERTY = 19
    NONCOLORED_PROPERTY = 20
    MORTGAGED = 21

    @staticmethod
    def is_set_attribute(attr: "TileAttribute") -> bool:
        return attr in [TileAttribute.SET1, TileAttribute.SET2, TileAttribute.SET3, TileAttribute.SET4,
                        TileAttribute.SET5, TileAttribute.SET6, TileAttribute.SET7, TileAttribute.SET8,
                        TileAttribute.RAILROAD, TileAttribute.UTILITY]


class Tile(ABC):
    # Fields: str name, TileAttribute[] attributes
    def __init__(self, name: str, **kwargs):
        self.name: str = name
        self.attributes: List[TileAttribute] = []

        if "attribute" in kwargs:
            self.attributes: List[TileAttribute] = [kwargs["attribute"]]
        elif "attributes" in kwargs:
            self.attributes: List[TileAttribute] = kwargs["attributes"]

    def __str__(self):
        return self.name


class BasicTile(Tile):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)


class Property(Tile, ABC):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    # Fields: int price, Player owner
    def __init__(self, name: str, price: int, **kwargs):
        super().__init__(name, **kwargs)
        self.price: int = price
        self.owner: Union[Player, None] = None  # Player
        self.mortgaged: bool = False

    def get_set_attribute(self) -> Union[TileAttribute, None]:
        for attr in self.attributes:
            if TileAttribute.is_set_attribute(attr):
                return attr
        return None

    def is_monopoly_completed(self) -> bool:
        return self.set_completion() == 1

    def set_completion(self) -> float:
        count: int = 0
        set_attr: TileAttribute = self.get_set_attribute()

        for prop in self.owner.properties:
            if prop.get_set_attribute() == set_attr:
                count += 1

        count: float = float(count)

        if set_attr == TileAttribute.SET1 or set_attr == TileAttribute.SET8 or set_attr == TileAttribute.UTILITY:
            return count / 2
        elif set_attr == TileAttribute.RAILROAD:
            return count / 4
        else:
            return count / 3

    def purchase(self, purchaser: Player):
        self.owner = purchaser
        purchaser.add_money(-self.price)
        purchaser.properties.append(self)

    def mortgage(self):
        self.mortgaged = True
        self.owner.add_money(int(0.5 * self.price))

    def unmortgage(self):
        self.mortgaged = False
        self.owner.add_money(int(-1.1 * 0.5 * self.price))  # Unmortgage = 110% of mortgage price

    def transfer_ownership(self, new_owner: Player):
        self.owner.properties.remove(self)
        self.owner = new_owner
        new_owner.properties.append(self)

    @abstractmethod
    def rent(self, **kwargs):
        pass


class ColoredProperty(Property):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    #       Property: int price, Player owner
    # Fields: int[] rents, int houses
    def __init__(self, name: str, price: int, rent_list: List[int], set_attribute: TileAttribute):
        super().__init__(name, price,
                         attributes=[TileAttribute.PROPERTY, set_attribute, TileAttribute.COLORED_PROPERTY])
        self.rents: List[int] = rent_list
        self.houses: int = 0

    def house_cost(self) -> int:
        set_attr: TileAttribute = self.get_set_attribute()  # TileAttribute
        if set_attr == TileAttribute.SET1 or set_attr == TileAttribute.SET2:
            return 50
        elif set_attr == TileAttribute.SET3 or set_attr == TileAttribute.SET4:
            return 100
        elif set_attr == TileAttribute.SET5 or set_attr == TileAttribute.SET6:
            return 150
        elif set_attr == TileAttribute.SET7 or set_attr == TileAttribute.SET8:
            return 200

    def rent(self, **kwargs) -> int:
        return self.rents[self.houses]

    def __str__(self):
        end_tag: Union[str, None] = None
        if self.is_monopoly_completed():
            if self.houses == 0:
                end_tag = "(Monopoly)"
            elif self.houses < 5:
                end_tag = "({} houses)".format(self.houses)
            else:
                end_tag = "(w/ Hotel)"
        return "{} {}".format(self.name, end_tag) if end_tag is not None else self.name


class NonColoredProperty(Property):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    # Fields: int price, Player owner
    def __init__(self, name: str, prop_type: TileAttribute):
        super().__init__(name, 200 if prop_type == TileAttribute.RAILROAD else 150)

    def rent(self, **kwargs) -> int:
        if TileAttribute.RAILROAD in self.attributes:
            count: int = 0
            for prop in self.owner.properties:
                if prop.get_set_attribute() == TileAttribute.RAILROAD:
                    count += 1
            return (2 ** (count - 1)) * 25
        else:
            count: int = 0
            for prop in self.owner.properties:
                if prop.get_set_attribute() == TileAttribute.UTILITY:
                    count += 1
            return kwargs["roll"] * (10 if count == 2 else 4)

    def __str__(self):
        end_tag: Union[str, None] = None
        if self.is_monopoly_completed():
            end_tag = "(Monopoly)"
        elif self.get_set_attribute() == TileAttribute.RAILROAD:
            end_tag = "(x{})".format(int(self.set_completion() * 4))
        elif self.get_set_attribute() == TileAttribute.UTILITY:
            end_tag = "(x{})".format(int(self.set_completion() * 2))

        return "{} {}".format(self.name, end_tag) if end_tag is not None else self.name


class MortgageManager:
    # Fields: Player client, TradeBroker broker

    def __init__(self, client: Player):
        self.client: Player = client
        self.broker: TradeBroker = TradeBroker(client)

    def force_mortgage(self, threshold: int) -> int:
        liquidated: int = 0

        liquidated += self.liquidate(self.class_f_properties(), threshold)
        if liquidated < threshold:
            self.liquidate(self.class_e_properties(), threshold)
            if liquidated < threshold:
                self.liquidate(self.class_d_properties(), threshold)
                if liquidated < threshold:
                    self.liquidate(self.class_c_properties(), threshold)
                    if liquidated < threshold:
                        self.liquidate(self.class_b_properties(), threshold)
                        if liquidated < threshold:
                            self.liquidate(self.class_a_properties(), threshold)
        return liquidated

    @staticmethod
    def liquidate(to_liquidate: List[Property], threshold: int) -> int:
        liquidated: int = 0
        for prop in to_liquidate:
            if not prop.mortgaged:
                prop.mortgaged = True
                liquidated += prop.price / 2

            if liquidated >= threshold:
                return liquidated
        return liquidated

    # Class A Properties - Colored properties in a monopoly set with a hotel on all properties in the set
    # Class B Properties - Colored properties with at least one hotel on the set
    # Class C Properties - Colored properties with at least one house on each property
    # Class D Properties - Properties as part of a completed monopoly set
    # Class E Properties - 50% or more completed sets
    # Class F Properties - Any other property

    def class_a_properties(self) -> List[Property]:
        out: List[Property] = []
        for prop in self.client.properties:
            if isinstance(prop, ColoredProperty) and prop.is_monopoly_completed():
                monopoly_set: List[Property] = [prop for prop in self.client.properties if
                                                prop.get_set_attribute() in prop.attributes]
                flag: bool = True
                for set_prop in monopoly_set:
                    if cast(ColoredProperty, set_prop).houses != 5:
                        flag = False
                if flag:
                    out.append(prop)
        return out

    def class_b_properties(self) -> List[Property]:
        out: List[Property] = []
        conflicts: List[Property] = self.class_a_properties()

        for prop in self.client.properties:
            if prop in conflicts:
                continue
            for set_prop in self.client.properties:
                if set_prop.get_set_attribute() == prop.get_set_attribute() and cast(ColoredProperty,
                                                                                     set_prop).houses == 5:
                    out.append(prop)
        return out

    def class_c_properties(self) -> List[Property]:
        out: List[Property] = []
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties()

        for prop in self.client.properties:
            if prop in conflicts:
                continue
            flag: bool = True
            for set_prop in self.client.properties:
                if cast(ColoredProperty, set_prop).houses == 0:
                    flag = False
            if flag:
                out.append(prop)
        return out

    def class_d_properties(self) -> List[Property]:
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties() + self.class_c_properties()
        return [prop for prop in self.client.properties if prop not in conflicts and prop.is_monopoly_completed()]

    def class_e_properties(self) -> List[Property]:
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties()
        conflicts += self.class_c_properties() + self.class_d_properties()

        return [prop for prop in self.client.properties if
                prop not in conflicts and self.broker.attribute_completion(prop.get_set_attribute()) >= 0.5]

    def class_f_properties(self) -> List[Property]:
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties() + self.class_c_properties()
        conflicts += self.class_d_properties() + self.class_e_properties()
        return [prop for prop in self.client.properties if prop not in conflicts]


class TradeBroker:
    # Fields: Player client

    @staticmethod
    def count_properties_with_attribute(player: Player, attr: TileAttribute) -> int:
        count: int = 0
        for prop in player.properties:
            if attr in prop.attributes:
                count += 1
        return count

    def __init__(self, client: Player):
        self.client: Player = client

    def assign_property_values(self) -> Dict[str, int]:
        values: Dict[str, int] = {}

        for prop in self.client.properties:
            value: int = prop.price

            if self.attribute_completion(prop.get_set_attribute()) == 1:
                if isinstance(prop, ColoredProperty):
                    value += self.houses_on_set(prop.get_set_attribute()) * prop.house_cost()
                value *= 4
            elif self.attribute_completion(prop.get_set_attribute()) >= 0.66:
                value *= 3
            elif self.attribute_completion(prop.get_set_attribute()) >= 0.5:
                value *= 2
            else:
                value *= 1.5
            values[prop.name] = int(value)

        return values

    def attribute_completion(self, attr: TileAttribute) -> float:
        count: int = 0
        total: int = 0

        for prop in self.client.properties:
            if attr in prop.attributes:
                count += 1

        for tile in self.client.game.board:
            if attr in tile.attributes:
                total += 1

        return float(count) / total if total != 0 else 0

    def attribute_completions(self) -> Dict[TileAttribute, float]:
        out: Dict[TileAttribute, float] = {}
        for prop in self.client.properties:
            out[prop.get_set_attribute()] = self.attribute_completion(prop.get_set_attribute())
        return out

    def houses_on_set(self, set_attr: TileAttribute) -> int:
        count: int = 0
        for prop in self.client.properties:
            if isinstance(prop, ColoredProperty) and set_attr in prop.attributes:
                count += prop.houses
        return count

    def most_wanted_set(self) -> TileAttribute:
        completions: Dict[TileAttribute, float] = self.attribute_completions()
        largest: Union[TileAttribute, None] = None

        for prop in self.client.properties:
            if largest is None:
                largest = prop.get_set_attribute()
            if completions[prop.get_set_attribute()] > completions[largest]:
                largest = prop.get_set_attribute()
        return largest

    def best_trader_match(self) -> Player:
        players: List[Player] = self.client.game.players
        best: Player = players[0]
        most_wanted_set: TileAttribute = self.most_wanted_set()

        for player in players:
            if self.count_properties_with_attribute(player, most_wanted_set) > self.count_properties_with_attribute(
                    best,
                    most_wanted_set):
                best = player
        return best


class TradeDeal:
    # Fields: Player player1, Player player2, Property[] player1acquisitions, Property[] player2acquisitions
    #         int compensation

    def __init__(self, p1: Player, p2: Player):
        self.player1: Player = p1
        self.player2: Player = p2
        self.player1acquisitions: List[Property] = []
        self.player2acquisitions: List[Property] = []
        self.compensation: int = 0

    def execute(self):
        if self.compensation > 0:
            Logger.log("{} payed {} ${}".format(self.player1, self.player2, self.compensation))
        elif self.compensation < 0:
            Logger.log("{} payed {} ${}".format(self.player2, self.player1, self.compensation))

        for prop in self.player1acquisitions:
            prop.transfer_ownership(self.player1)

        for prop in self.player2acquisitions:
            prop.transfer_ownership(self.player2)

        self.player1.add_money(-self.compensation)
        self.player2.add_money(self.compensation)


class TradeManager:
    @staticmethod
    def run_best_trade(client: Player):
        # Make sure at least 14 properties have been bought
        unowned_properties: List[Property] = [curr_tile for curr_tile in client.game.board if
                                              isinstance(curr_tile, Property) and not curr_tile.owner]
        if len(unowned_properties) < 14:
            return
        del unowned_properties

        broker: TradeBroker = TradeBroker(client)
        other_player: Player = broker.best_trader_match()
        other_broker: TradeBroker = TradeBroker(client)
        deal: TradeDeal = TradeDeal(client, other_player)
        receiving: TileAttribute = broker.most_wanted_set()
        giving: TileAttribute = other_broker.most_wanted_set()

        deal.player1acquisitions = [prop for prop in other_player.properties if receiving in prop.attributes]
        deal.player2acquisitions = [prop for prop in client.properties if giving in prop.attributes]

        player1value: int = 0
        player2value: int = 0

        values: Dict[str, int] = broker.assign_property_values()
        for prop in deal.player2acquisitions:
            player1value += values[prop.name] if prop.name in values else 0

        values: Dict[str, int] = other_broker.assign_property_values()
        for prop in deal.player1acquisitions:
            player2value += values[prop.name] if prop.name in values else 0

        deal.compensation = player2value - player1value

        deal.execute()


def build_board():
    chance_label: str = "Chance"
    chest_label: str = "Community Chest"
    return [BasicTile("Go", attribute=TileAttribute.GO),
            ColoredProperty("Mediterranean Avenue", 60, [2, 10, 30, 90, 160, 250],
                            TileAttribute.SET1),
            BasicTile(chest_label, attribute=TileAttribute.CHEST),
            ColoredProperty("Baltic Avenue", 60, [4, 20, 60, 180, 320, 450], TileAttribute.SET1),
            BasicTile("Tax", attribute=TileAttribute.TAX),
            NonColoredProperty("Reading Railroad", TileAttribute.RAILROAD),
            ColoredProperty("Oriental Avenue", 100, [6, 30, 90, 270, 400, 550],
                            TileAttribute.SET2),
            BasicTile(chance_label, attribute=TileAttribute.CHANCE),
            ColoredProperty("Vermont Avenue", 100, [6, 30, 90, 270, 400, 550], TileAttribute.SET2),
            ColoredProperty("Connecticut Avenue", 120, [8, 40, 100, 300, 450, 600],
                            TileAttribute.SET2),
            BasicTile("Jail", attribute=TileAttribute.JAIL),
            ColoredProperty("St. Charles Place", 140, [10, 50, 150, 450, 625, 750],
                            TileAttribute.SET3),
            NonColoredProperty("Electric Company", TileAttribute.UTILITY),
            ColoredProperty("States Avenue", 140, [10, 50, 150, 450, 625, 750],
                            TileAttribute.SET3),
            ColoredProperty("Virginia Avenue", 160, [12, 60, 180, 500, 700, 900],
                            TileAttribute.SET3),
            NonColoredProperty("Pennsylvania Railroad", TileAttribute.RAILROAD),
            ColoredProperty("St. James Place", 180, [14, 70, 200, 550, 750, 950],
                            TileAttribute.SET4),
            BasicTile(chest_label, attribute=TileAttribute.CHEST),
            ColoredProperty("Tennessee Avenue", 180, [14, 70, 200, 550, 750, 950],
                            TileAttribute.SET4),
            ColoredProperty("New York Avenue", 200, [16, 80, 220, 600, 800, 1000],
                            TileAttribute.SET4),
            BasicTile("Free Parking", attribute=TileAttribute.FREE_PARKING),
            ColoredProperty("Kentucky Avenue", 220, [18, 90, 250, 700, 875, 1050],
                            TileAttribute.SET5),
            BasicTile(chance_label, attribute=TileAttribute.CHANCE),
            ColoredProperty("Indiana Avenue", 220, [18, 90, 250, 700, 875, 1050],
                            TileAttribute.SET5),
            ColoredProperty("Illinois Avenue", 240, [20, 100, 300, 750, 925, 1100],
                            TileAttribute.SET5),
            NonColoredProperty("B. & O. Railroad", TileAttribute.RAILROAD),
            ColoredProperty("Atlantic Avenue", 260, [22, 110, 330, 800, 975, 1150],
                            TileAttribute.SET6),
            ColoredProperty("Ventnor Avenue", 260, [22, 110, 330, 800, 975, 1150],
                            TileAttribute.SET6),
            NonColoredProperty("Waterworks", TileAttribute.RAILROAD),
            ColoredProperty("Marvin Gardens", 280, [24, 120, 360, 850, 1025, 1200],
                            TileAttribute.SET6),
            BasicTile("Go to Jail", attribute=TileAttribute.GO_TO_JAIL),
            ColoredProperty("Pacific Avenue", 300, [26, 130, 390, 900, 1100, 1275],
                            TileAttribute.SET7),
            ColoredProperty("North Carolina Avenue", 300, [26, 130, 390, 900, 1100, 1275],
                            TileAttribute.SET7),
            BasicTile(chest_label, attribute=TileAttribute.CHEST),
            ColoredProperty("Pennsylvania Avenue", 320, [28, 150, 450, 1000, 1200, 1400],
                            TileAttribute.SET7),
            NonColoredProperty("Short Line", TileAttribute.RAILROAD),
            BasicTile(chance_label, attribute=TileAttribute.CHANCE),
            ColoredProperty("Park Place", 350, [35, 175, 500, 1100, 1300, 1500],
                            TileAttribute.SET8),
            BasicTile("Tax", attribute=TileAttribute.TAX),
            ColoredProperty("Boardwalk", 400, [50, 200, 600, 1400, 1700, 2000],
                            TileAttribute.SET8)]
