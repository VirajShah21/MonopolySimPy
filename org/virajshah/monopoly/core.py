from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Union, Dict, cast

from org.virajshah.monopoly.logger import Logger
from org.virajshah.monopoly.records import TurnHistoryRecord
from random import randrange
import random

from org.virajshah.monopoly.tracker import InvestmentTracker

JAIL_INDEX = 30


class MonopolyGame:
    def __init__(self, **kwargs):
        """
        Initialize a MonopolyGame object

        :param kwargs:
            players=List[str]: names of players to initialize the game with
        """
        self.board: List[Tile] = build_board()  # Tile[]
        self.players: List[Player] = []
        self.bankrupted_players: List[Player] = []
        self.curr_player: int = -1
        self.turn_number: int = 0
        self.investment_tracker: InvestmentTracker = InvestmentTracker()

        # Check if argument players=List[str] was passed
        # Then create players + add to game with provided names
        if "players" in kwargs:
            for player in kwargs["players"]:
                self.players.append(Player(player, self))

    def add_player(self, player: "Player") -> None:
        """
        Add a player to the list of current active players

        :param player: The player to add
        :return: None
        """
        self.players.append(player)

    @staticmethod
    def build_houses(player: "Player"):
        mortgager: MortgageManager = MortgageManager(player)
        to_build: List[Property]
        class_b: List[Property] = mortgager.class_b_properties()
        class_c: List[Property] = mortgager.class_c_properties()
        class_d: List[Property] = mortgager.class_d_properties()
        class_e: List[Property] = mortgager.class_e_properties()
        class_f: List[Property] = mortgager.class_f_properties()

        if player.configuration.mortgage_to_build and player.configuration.quick_builder:
            to_build = class_b + class_c + class_d
            mortgager.liquidate_all(class_e + class_f)
        elif player.configuration.mortgage_to_build:
            to_build: List[Property] = class_b or class_c or class_d
            mortgager.liquidate_all(class_f if len(class_f) != 0 else class_e)
        elif player.configuration.quick_builder:
            to_build: List[Property] = class_b + class_c + class_d
        else:
            to_build: List[Property] = class_b or class_c or class_d

        for prop in to_build:
            assert isinstance(prop, ColoredProperty)
            house_cost: int = prop.house_cost()
            insurance: int = player.configuration.insurance_amount(player.game)
            while prop.houses < 5 and player.balance - house_cost > insurance:
                prop.houses += 1
                player.add_money(-house_cost)
            prop.distribute_houses()

    def player_landed_on_property(self, player: "Player", turn: TurnHistoryRecord):
        prop: Property = cast(Property, self.board[player.position])

        if prop.owner is None and player.balance - prop.price >= player.configuration.insurance_amount(self):
            prop.purchase(player)
            turn.new_properties.append(prop.name)
            self.investment_tracker.track_property(prop.name, prop.owner.name, self.turn_number, prop.price)
            Logger.log("{} purchased {} for ${}".format(player.name, prop.name, prop.price), type="transaction")
        elif prop.owner is not None and prop.owner != player:
            rent_due = prop.rent(roll=(turn.dice_roll1 + turn.dice_roll2))
            player.send_money(rent_due, prop.owner)
            self.investment_tracker.rent_collected(prop.name, player.name, rent_due)
            Logger.log("{} payed {} ${} for rent on {}".format(player, prop.owner, rent_due, prop),
                       type="transaction")

    def run_next_turn(self) -> None:
        """
        Run the turn of the next player

        :return: None
        """

        if len(self.players) == 0:
            Logger.log("There are no remaining players")
            return

        self.curr_player += 1

        if self.curr_player >= len(self.players):
            self.curr_player = 0

        player: Player = self.players[self.curr_player]
        turn: TurnHistoryRecord = TurnHistoryRecord()
        self.turn_number += 1

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
            self.player_landed_on_property(player, turn)

        TradeBroker(player).run_best_trade()

        MonopolyGame.build_houses(player)

        turn.recent_balance = player.balance

        if player.balance < 0:
            mortgager: MortgageManager = MortgageManager(player)
            mortgager.force_mortgage(-player.balance)

        if player.balance < 0:
            for prop in player.properties:
                prop.mortgaged = False
                prop.owner = None
            player.properties.clear()
            self.bankrupted_players.append(player)
            self.players.remove(player)
            Logger.log("{} is now bankrupt (${}). Removing from the game.".format(player.name, player.balance),
                       type="bankrupted")

        player.turn_history.append(turn)
        self.log_all_player_updates()

    def log_all_player_updates(self) -> None:
        """
        Log the status of each active player to org.virajshah.monopoly.Logger

        :return: None
        """
        to_log = ""
        for p in self.players:
            to_log += "{} has ${} and {}\n".format(p.name, p.balance, [str(prop) for prop in p.properties])
        Logger.log(to_log, type="player-update")


class Player:
    def __init__(self, name: str, game: MonopolyGame):
        """
        Initialize a monopoly player

        :param name: The player's name
        :param game: The game which the player is currently playing
        """
        self.name: str = name
        self.balance: int = 1500
        self.position: int = 0
        self.turn_history: List[TurnHistoryRecord] = []
        self.properties: List[Property] = []
        self.prisoner: bool = False
        self.game: MonopolyGame = game  # Game is assigned by MonopolyGame
        self.configuration: PlayerConfiguration = PlayerConfiguration()

    def send_money(self, amount: int, other_player: "Player") -> None:
        """
        Send money from self to another player

        :param amount: The amount of money to send
        :param other_player: The player to receive the money
        :return: None
        """
        self.add_money(-amount)
        other_player.add_money(amount)

    def add_money(self, amount: int) -> None:
        """
        Add money to player's (self) balance

        :param amount: The amount of money to add
        :return: None
        """
        self.balance += amount

    def __str__(self):
        """
        :return: The player's name
        """
        return self.name


class PlayerConfiguration:
    def __init__(self):
        """
        Generate a random player configuration
        """
        self.mortgage_to_build: bool = True if randrange(0, 2) else False
        self.quick_builder: bool = True if randrange(0, 2) else False
        self.insurance_rate: float = random.random() / 4

    def insurance_amount(self, game: MonopolyGame) -> int:
        """
        Get the amount of money which the user would like
        to use as insurance

        :param game: The wrapping game
        :return: The amount of insurance money
        """
        circulation: int = 0
        for player in game.players:
            circulation += player.balance
        return int(self.insurance_rate * circulation)


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
        """
        :param attr: TileAttribute to test
        :return: True if the TileAttribute describes a set
            (color group or utility/railroad type
        """
        return attr in [TileAttribute.SET1, TileAttribute.SET2, TileAttribute.SET3, TileAttribute.SET4,
                        TileAttribute.SET5, TileAttribute.SET6, TileAttribute.SET7, TileAttribute.SET8,
                        TileAttribute.RAILROAD, TileAttribute.UTILITY]


class Tile(ABC):
    def __init__(self, name: str, **kwargs):
        """
        The superclass of all Tiles

        :param name: The name of the tile
        :param kwargs:
            attribute=TileAttribute: an attribute to add to the tile
            attribute=List[TileAttribute]: a list of attributes to add
        """
        self.name: str = name
        self.attributes: List[TileAttribute] = []

        if "attribute" in kwargs:
            self.attributes: List[TileAttribute] = [kwargs["attribute"]]
        elif "attributes" in kwargs:
            self.attributes: List[TileAttribute] = kwargs["attributes"]

    def __str__(self):
        """
        :return: The tile's (self) name
        """
        return self.name


class BasicTile(Tile):
    def __init__(self, name: str, **kwargs):
        """
        Useless tiles are an instance of BasicTile

        :param name: The name of the tile
        :param kwargs:
            attribute=TileAttribute: an attribute to add to the tile
            attribute=List[TileAttribute]: a list of attributes to add
        """
        super().__init__(name, **kwargs)


class Property(Tile, ABC):
    def __init__(self, name: str, price: int, **kwargs):
        """
        Initialize a Property tile (Colored properties, railroads, and utilities)

        :param name: The name of the property
        :param price: The cost to purchase the property
        :param kwargs:
            attribute=TileAttribute: an attribute to add to the tile
            attribute=List[TileAttribute]: a list of attributes to add
        """
        super().__init__(name, **kwargs)
        self.price: int = price
        self.owner: Union[Player, None] = None  # Player
        self.mortgaged: bool = False

    def get_set_attribute(self) -> Union[TileAttribute, None]:
        """
        Get the TileAttribute which describes `self` belongs in
        :return: The TileAttribute describing the properties set.
            Return value should be checked for None.
        """
        for attr in self.attributes:
            if TileAttribute.is_set_attribute(attr):
                return attr
        return None

    def is_monopoly_completed(self) -> bool:
        """
        :return: True if the monopoly set is complete for this property's set
        """
        return self.set_completion() == 1

    def set_completion(self) -> float:
        """
        :return: A float representing how complete the current set is.
            Calculated relative to properties owned by the owner
            and the set which they belong to.
        """
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

    def purchase(self, purchaser: Player) -> None:
        """
        Make a player purchase this property. This assigns the owner
        of this property to the new owner, deducts the balance from
        the owner and adds the property to the owner's list of
        properties.

        :param purchaser: The player purchasing the property
        :return: None
        """
        self.owner = purchaser
        purchaser.add_money(-self.price)
        purchaser.properties.append(self)

    def mortgage(self) -> None:
        """
        Mortgages a property and reimburses the player.

        :return: None
        """
        self.mortgaged = True
        self.owner.add_money(int(0.5 * self.price))

    def unmortgage(self) -> None:
        """
        Unmortgage a property and charge the player.

        :return: None
        """
        self.mortgaged = False
        self.owner.add_money(int(-1.1 * 0.5 * self.price))  # Unmortgage = 110% of mortgage price

    def transfer_ownership(self, new_owner: Player) -> None:
        """
        Transfer the ownership of this property from the current
        owner to a new owner. Also transfers the property from
        their respective property lists.

        :param new_owner: The new owner of the property
        :return: None
        """
        self.owner.properties.remove(self)
        self.owner = new_owner
        new_owner.properties.append(self)

    @abstractmethod
    def rent(self, **kwargs) -> int:
        """
        Should return the rent value for the appropriate type
        of property.

        :param kwargs: Defined by subclasses
        :return: The amount due on the property's rent
        """
        pass


class ColoredProperty(Property):
    def __init__(self, name: str, price: int, rent_list: List[int], set_attribute: TileAttribute):
        """
        Initialize a colored property. These are properties
        with an assigned color. Does not include railroads
        and utility's.

        :param name: The name of the property
        :param price: The cost to purchase the property from the bank
        :param rent_list: The list of rent values per house (rent_list[5] = w/ hotel)
        :param set_attribute: The set which this property belongs to
        """
        super().__init__(name, price,
                         attributes=[TileAttribute.PROPERTY, set_attribute, TileAttribute.COLORED_PROPERTY])
        self.rents: List[int] = rent_list
        self.houses: int = 0

    def house_cost(self) -> int:
        """
        :return: The cost to build a single house on this property
        """

        set_attr: TileAttribute = self.get_set_attribute()  # TileAttribute
        if set_attr == TileAttribute.SET1 or set_attr == TileAttribute.SET2:
            return 50
        elif set_attr == TileAttribute.SET3 or set_attr == TileAttribute.SET4:
            return 100
        elif set_attr == TileAttribute.SET5 or set_attr == TileAttribute.SET6:
            return 150
        elif set_attr == TileAttribute.SET7 or set_attr == TileAttribute.SET8:
            return 200

    def distribute_houses(self) -> None:
        """
        Distribute the number of houses on this set amongst all properties
        on the same set

        :return: None
        """
        set_attr: TileAttribute = self.get_set_attribute()

        min_houses: int = 5  # These values are reversed
        max_houses: int = 0  # Think about why it makes sense
        min_prop: Union[Property, None] = None
        max_prop: Union[Property, None] = None

        for prop in self.owner.properties:
            assert isinstance(prop, ColoredProperty)
            if prop.get_set_attribute() == set_attr:
                if prop.houses < min_houses:
                    min_houses = prop.houses
                    min_prop = prop
                if prop.houses > max_houses:
                    max_houses = prop.houses
                    max_prop = prop

        if max_houses - min_houses > 1:
            min_prop.houses += 1
            max_prop.houses -= 1
            self.distribute_houses()

    def rent(self, **kwargs) -> int:
        """
        :param kwargs: Empty parameter list
        :return: The amount of rent due on the property
        """
        return self.rents[self.houses]

    def __str__(self):
        """
        :return: The name of the property and the number of houses/hotel.
        """

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
    def __init__(self, name: str, prop_type: TileAttribute):
        """
        Initialize a property which is not a colored property.
        This only includes railroads and utilities.

        :param name: The name of the type
        :param prop_type: Either TileAttribute.{RAILROAD or UTILITY}
        """
        super().__init__(name, 200 if prop_type == TileAttribute.RAILROAD else 150)

    def rent(self, **kwargs) -> int:
        """
        Get the amount of rent owned the property

        :param kwargs:
            roll=int: The sum of both dice rolls
        :return: The amount of money due on rent on this property
        """

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
        """
        :return: The property name and how many of the set are owned
        """

        end_tag: Union[str, None] = None
        if self.is_monopoly_completed():
            end_tag = "(Monopoly)"
        elif self.get_set_attribute() == TileAttribute.RAILROAD:
            end_tag = "(x{})".format(int(self.set_completion() * 4))
        elif self.get_set_attribute() == TileAttribute.UTILITY:
            end_tag = "(x{})".format(int(self.set_completion() * 2))

        return "{} {}".format(self.name, end_tag) if end_tag is not None else self.name


class MortgageManager:
    def __init__(self, client: Player):
        """
        :param client: The player to manage
        """
        self.client: Player = client
        self.broker: TradeBroker = TradeBroker(client)

    def force_mortgage(self, threshold: int) -> int:
        """
        Force a mortgage until a specified amount of money
        has been collected.

        :param threshold: The amount of money required from
            the mortgages
        :return: The amount money obtained from the mortgages
        """
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
    def sell_houses(prop: Property) -> int:
        """
        Sell all houses on the specified property

        :param prop: The property to sell houses on
        :return: The number of sold houses
        """
        if isinstance(prop, ColoredProperty) and prop.houses > 0:
            prop.owner.add_money(int(0.5 * prop.houses * prop.house_cost()))
            sold: int = prop.houses
            prop.houses = 0
            return sold
        return 0

    @staticmethod
    def liquidate(to_liquidate: List[Property], threshold: int) -> int:
        """
        Liquidate a list of properties up to a specified threshold.

        :param to_liquidate: The list of properties to mortgage
        :param threshold: The specified threshold to quit liquidation
        :return: The value of liquidated properties
        """
        liquidated: int = 0
        for prop in to_liquidate:
            if not prop.mortgaged:
                MortgageManager.sell_houses(prop)
                prop.mortgage()
                liquidated += prop.price / 2

            if liquidated >= threshold:
                return liquidated
        return liquidated

    @staticmethod
    def liquidate_all(to_liquidate: List[Property]):
        """
        Forcefully liquidate a list of properties

        :param to_liquidate: The list of properties to mortgage
        :return: Amount of money received from the mortgages
        """
        liquidated: int = 0
        for prop in to_liquidate:
            if not prop.mortgaged:
                MortgageManager.sell_houses(prop)
                prop.mortgage()
                liquidated += prop.price / 2
        return liquidated

    def class_a_properties(self) -> List[Property]:
        """
        :return: Colored properties in a monopoly set with a hotel on all properties in the set
        """
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
        """
        :return: Colored properties with at least one hotel on the set
        """
        out: List[Property] = []
        conflicts: List[Property] = self.class_a_properties()

        for prop in self.client.properties:
            if prop in conflicts:
                continue
            prop_attr: TileAttribute = prop.get_set_attribute()
            for set_prop in self.client.properties:
                if set_prop.get_set_attribute() == prop_attr and cast(ColoredProperty, set_prop).houses == 5:
                    out.append(prop)
        return out

    def class_c_properties(self) -> List[Property]:
        """
        :return: Colored properties with at least one house on each property
        """
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
        """
        :return:  Properties as part of a completed monopoly set
        """
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties() + self.class_c_properties()
        return [prop for prop in self.client.properties if prop not in conflicts and prop.is_monopoly_completed()]

    def class_e_properties(self) -> List[Property]:
        """
        :return: 50% or more completed sets
        """
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties()
        conflicts += self.class_c_properties() + self.class_d_properties()

        return [prop for prop in self.client.properties if
                prop not in conflicts and self.broker.attribute_completion(prop.get_set_attribute()) >= 0.5]

    def class_f_properties(self) -> List[Property]:
        """
        :return: All inferior properties
        """
        conflicts: List[Property] = self.class_a_properties() + self.class_b_properties() + self.class_c_properties()
        conflicts += self.class_d_properties() + self.class_e_properties()
        return [prop for prop in self.client.properties if prop not in conflicts]


class TradeBroker:
    @staticmethod
    def count_properties_with_attribute(player: Player, attr: TileAttribute) -> int:
        """
        Count the number of properties with a specified attribute are
        owned by the client.

        :param player: The player acting as the static client
        :param attr: The TileAttribute to calculate
        :return: The number of properties with the same attribute
            which have the same owner
        """
        count: int = 0
        for prop in player.properties:
            if attr in prop.attributes:
                count += 1
        return count

    def __init__(self, client: Player):
        """
        :param client: The broker's client
        """
        self.client: Player = client

    def assign_property_values(self) -> Dict[str, int]:
        """
        Assign implicit value to the properties owned by the client

        :return: A dictionary mapping the property's name to it's value
        """

        values: Dict[str, int] = {}

        for prop in self.client.properties:
            value: int = prop.price
            completion: float = self.attribute_completion(prop.get_set_attribute())
            if completion == 1:
                if isinstance(prop, ColoredProperty):
                    value += self.houses_on_set(prop.get_set_attribute()) * prop.house_cost()
                value *= 4
            elif completion >= 0.66:
                value *= 3
            elif completion >= 0.5:
                value *= 2
            else:
                value *= 1.5
            values[prop.name] = int(value)

        return values

    def attribute_completion(self, attr: TileAttribute) -> float:
        """
        Calculate the attribute completion for a TileAttribute

        :param attr: The attribute to calculate completion
        :return: The attributes set completion
        """

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
        """
        Calculate the attribute completion for all properties belong
        to the client.

        :return: A dictionary mapping the TileAttribute to a float
            representing the attribute completion
        """
        out: Dict[TileAttribute, float] = {}
        for prop in self.client.properties:
            if prop.get_set_attribute() not in out:
                out[prop.get_set_attribute()] = self.attribute_completion(prop.get_set_attribute())
        return out

    def houses_on_set(self, set_attr: TileAttribute) -> int:
        """
        Compute the number of houses on the set (not just a property)

        :param set_attr: The TileAttribute describing a colored property set
        :return: The number of houses on the specified set
        """
        count: int = 0
        for prop in self.client.properties:
            if isinstance(prop, ColoredProperty) and set_attr in prop.attributes:
                count += prop.houses
        return count

    def most_wanted_set(self) -> TileAttribute:
        """
        :return: The TileAttribute of the most wanted set
        """

        completions: Dict[TileAttribute, float] = self.attribute_completions()
        largest: Union[TileAttribute, None] = None

        for prop in self.client.properties:
            if largest is None:
                largest = prop.get_set_attribute()
            if completions[prop.get_set_attribute()] > completions[largest]:
                largest = prop.get_set_attribute()
        return largest

    def best_trader_match(self) -> Player:
        """
        :return: The player that offers the best trade for the client
        """

        players: List[Player] = self.client.game.players
        best: Player = players[0] if players[0] != self.client else players[1]
        most_wanted_set: TileAttribute = self.most_wanted_set()

        for player in players:
            match_props_with_attr: int = self.count_properties_with_attribute(best, most_wanted_set)
            self_props_with_attr: int = self.count_properties_with_attribute(player, most_wanted_set)
            if player != self.client and self_props_with_attr > match_props_with_attr:
                best = player
        return best

    def run_best_trade(self) -> bool:
        """
        Run the best trade for the client. Only runs if at least
        14 properties have been bought.

        :return: True if the trade was successful, False otherwise
        """
        client: Player = self.client
        # Make sure at least 14 properties have been bought
        unowned_properties: List[Property] = [curr_tile for curr_tile in client.game.board if
                                              isinstance(curr_tile, Property) and not curr_tile.owner]
        if len(unowned_properties) < 14:
            return False
        del unowned_properties

        broker: TradeBroker = TradeBroker(client)
        other_player: Player = broker.best_trader_match()
        other_broker: TradeBroker = TradeBroker(client)
        deal: TradeDeal = TradeDeal(client, other_player)
        receiving: TileAttribute = broker.most_wanted_set()
        giving: TileAttribute = other_broker.most_wanted_set()

        if receiving is not None and giving is not None and receiving != giving:
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

            Logger.log("Trade Deal\n==========\n" + str(deal))
            deal.execute()
            return True
        return False


class TradeDeal:
    def __init__(self, p1: Player, p2: Player):
        """
        A container for trade data.
        Includes one method (execute) to execute the trade.

        :param p1: Player 1 (client of the broker creating the TradeDeal)
        :param p2: Player 2
        """
        self.player1: Player = p1
        self.player2: Player = p2
        self.player1acquisitions: List[Property] = []
        self.player2acquisitions: List[Property] = []
        self.compensation: int = 0

    def execute(self) -> None:
        """
        FORCES the execution of a trade
        :return: None
        """

        if self.compensation > 0:
            Logger.log("{} payed {} ${}".format(self.player1, self.player2, self.compensation))
        elif self.compensation < 0:
            Logger.log("{} payed {} ${}".format(self.player2, self.player1, self.compensation))

        for prop in self.player1acquisitions:
            prop.transfer_ownership(self.player1)
            avg_price: int = sum([prop.price for prop in self.player2acquisitions]) + self.compensation
            avg_price /= len(self.player1acquisitions)
            prop.owner.game.investment_tracker.track_property(prop.name, prop.owner.name, prop.owner.game.turn_number,
                                                              avg_price)

        for prop in self.player2acquisitions:
            prop.transfer_ownership(self.player2)
            avg_price: int = sum([prop.price for prop in self.player1acquisitions]) - self.compensation
            avg_price /= len(self.player2acquisitions)
            prop.owner.game.investment_tracker.track_property(prop.name, prop.owner.name, prop.owner.game.turn_number,
                                                              avg_price)

        self.player1.add_money(-self.compensation)
        self.player2.add_money(self.compensation)

    def __str__(self):
        """
        :return: The transactions involved in the deal
        """
        return "{0} acquires {1}\n{2} acquires {3}\nNet transfer: {0} --[ ${4} ]--> {2}" \
            .format(self.player1.name,
                    self.player1acquisitions,
                    self.player2.name,
                    self.player2acquisitions,
                    self.compensation)


def build_board() -> List[Tile]:
    """
    :return: A list of Tile objects which represent a
        Monopoly Game board
    """
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
