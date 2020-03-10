from abc import ABC, abstractmethod
from enum import Enum

CHANCE_LABEL = "Chance"
CHEST_LABEL = "Community Chest"


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


class Tile(ABC):
    # Fields: str name, TileAttribute[] attributes
    def __init__(self, name, **kwargs):
        self.name = name
        if "attribute" in kwargs:
            self.attributes = [kwargs["attribute"]]
        elif "attributes" in kwargs:
            self.attributes = kwargs["attributes"]
        else:
            self.attributes = []

    def __str__(self):
        return self.name


class BasicTile(Tile):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)


class Property(ABC, Tile):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    # Fields: int price, Player owner
    def __init__(self, name, price, **kwargs):
        super().__init__(name, kwargs)
        self.price = price
        self.owner = None  # Player

    def set_attribute(self):
        for attr in self.attributes:
            if TileAttribute.is_set_attribute(attr):
                return attr
        return None

    def is_monopoly_completed(self):
        count = 0
        for prop in self.owner.properties:
            if prop.set_attribute() == self.set_attribute():
                count += 1

        set_attr = self.set_attribute()

        if set_attr == TileAttribute.SET1 or set_attr == TileAttribute.SET8 or set_attr == TileAttribute.UTILITY:
            return count == 2
        elif set_attr == TileAttribute.RAILROAD:
            return count == 4
        else:
            return count == 3

    def mortgage(self):
        pass  # implement this

    @abstractmethod
    def rent(self, **kwargs):
        pass


class ColoredProperty(Property):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    #       Property: int price, Player owner
    # Fields: int[] rents, int houses
    def __init__(self, name, price, rent_list, set_attribute):
        super().__init__(name, price,
                         attributes=[TileAttribute.PROPERTY, set_attribute, TileAttribute.COLORED_PROPERTY])
        self.rents = rent_list
        self.houses = 0

    def house_cost(self):
        set_attr = self.set_attribute()  # TileAttribute
        if set_attr == TileAttribute.SET1 or set_attr == TileAttribute.SET2:
            return 50
        elif set_attr == TileAttribute.SET3 or set_attr == TileAttribute.SET4:
            return 100
        elif set_attr == TileAttribute.SET5 or set_attr == TileAttribute.SET6:
            return 150
        elif set_attr == TileAttribute.SET7 or set_attr == TileAttribute.SET8:
            return 200


class NonColoredProperty(Property):
    # Inherited Fields
    #       Tile: str name, TileAttribute[] attributes
    # Fields: int price, Player owner
    def __init__(self, name, prop_type):
        super(name, 200 if prop_type == TileAttribute.RAILROAD else 150)


def build_board():
    # return [
    #     BasicTile("Go", Attribute.GO),
    #     ColoredProperty("Mediterranean Avenue", 60, [2, 10, 30, 90, 160, 250], Attribute.SET1),
    #     BasicTile(CHEST_LABEL, TileAttribute.CHEST),
    #     ColoredProperty("Baltic Avenue", 60, [4, 20, 60, 180, 320, 450], TileAttribute.SET1)
    # ]

    return [BasicTile("Go", attribute=TileAttribute.GO),
            ColoredProperty("Mediterranean Avenue", 60, [2, 10, 30, 90, 160, 250],
                            TileAttribute.SET1),
            BasicTile(CHEST_LABEL, attribute=TileAttribute.CHEST),
            ColoredProperty("Baltic Avenue", 60, [4, 20, 60, 180, 320, 450], TileAttribute.SET1),
            BasicTile("Tax", attribute=TileAttribute.TAX),
            NonColoredProperty("Reading Railroad", TileAttribute.RAILROAD),
            ColoredProperty("Oriental Avenue", 100, [6, 30, 90, 270, 400, 550],
                            TileAttribute.SET2),
            BasicTile(CHANCE_LABEL, attribute=TileAttribute.CHANCE),
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
            BasicTile(CHEST_LABEL, attribute=TileAttribute.CHEST),
            ColoredProperty("Tennessee Avenue", 180, [14, 70, 200, 550, 750, 950],
                            TileAttribute.SET4),
            ColoredProperty("New York Avenue", 200, [16, 80, 220, 600, 800, 1000],
                            TileAttribute.SET4),
            BasicTile("Free Parking", attribute=TileAttribute.FREE_PARKING),
            ColoredProperty("Kentucky Avenue", 220, [18, 90, 250, 700, 875, 1050],
                            TileAttribute.SET5),
            BasicTile(CHANCE_LABEL, attribute=TileAttribute.CHANCE),
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
            BasicTile(CHEST_LABEL, attribute=TileAttribute.CHEST),
            ColoredProperty("Pennsylvania Avenue", 320, [28, 150, 450, 1000, 1200, 1400],
                            TileAttribute.SET7),
            NonColoredProperty("Short Line", TileAttribute.RAILROAD),
            BasicTile(CHANCE_LABEL, attribute=TileAttribute.CHANCE),
            ColoredProperty("Park Place", 350, [35, 175, 500, 1100, 1300, 1500],
                            TileAttribute.SET8),
            BasicTile("Tax", attribute=TileAttribute.TAX),
            ColoredProperty("Boardwalk", 400, [50, 200, 600, 1400, 1700, 2000],
                            TileAttribute.SET8)]
