from . import utils
from .tiles import ColoredProperty


class MortgageManager:
    def __init__(self, client):
        self.client = client
        self.broker = TradeBroker(client)

    def smart_mortgage(self, threshold):
        liquidate = 0
        toLiquidate = self.class_a_properties()
        # TODO: finish this method

    '''
         Class A Properties - Colored properties in a monopoly set with a hotel on all properties in the set
         Class B Properties - Colored properties with at least one hotel on the set
         Class C Properties - Colored properties with at least one house on each property
         Class D Properties - Properties as part of a completed monopoly set
         Class E Properties - 50% or more completed sets
         Class F Properties - Any other property
    '''

    def class_a_properties(self):
        out = []
        for prop in self.client.properties:
            if isinstance(prop, ColoredProperty) and prop.is_monopoly_completed():
                monopoly_set = self.client_properties_by_attribute(prop.set_attribute())
                flag = True
                for set_prop in monopoly_set:
                    if set_prop.houses != 5:
                        flag = False
                if flag:
                    out.append(prop)
        return out

    def class_b_properties(self):
        out = []
        conflicts = self.class_a_properties()
        for prop in self.client.properties:
            if prop in conflicts:
                continue
            for set_prop in self.client.properties:
                if set_prop.set_attribute() == prop.set_attribute() and set_prop.houses == 5:
                    out.append(prop)
        return out

    def class_c_properties(self):
        out = []
        conflicts = utils.merge(self.class_a_properties(), self.class_b_properties())

        for prop in self.client.properties:
            if prop in conflicts:
                continue
            flag = True
            for set_prop in self.client.properties:
                if set_prop.houses == 0:
                    flag = False
            if flag:
                out.append(prop)
        return out

    def class_d_properties(self):
        out = []
        conflicts = utils.merge(self.class_a_properties(), self.class_b_properties(), self.class_c_properties())

        for prop in self.client.properties:
            if prop not in conflicts and prop.is_monopoly_completed():
                out.append(prop)
        return out

    def class_e_properties(self):
        out = []
        conflicts = utils.merge(self.class_a_properties(), self.class_b_properties(), self.class_c_properties(),
                                self.class_d_properties())

        for prop in self.client.properties:
            if prop not in conflicts and self.broker.attribute_completion(prop.set_attribute()) >= 0.5:
                out.append(prop)
        return out

    def class_f_properties(self):
        out = []
        conflicts = utils.merge(self.class_a_properties(), self.class_b_properties(), self.class_c_properties(),
                                self.class_d_properties(), self.class_e_properties())

        for prop in self.client.properties:
            if prop not in conflicts:
                out.append(prop)
        return out

    def client_properties_by_attribute(self, attribute):
        out = []
        for prop in self.client.properties:
            if attribute in prop.attributes:
                out.append(prop)
        return out


class TradeBroker:
    @staticmethod
    def count_properties_with_attribute(player, attr):
        count = 0
        for prop in player.properties:
            if attr in prop.attributes:
                count += 1
        return count

    def __init__(self, client):
        self.client = client

    def assign_property_values(self):
        values = {}

        for prop in self.client.properties:
            value = prop.price

            if self.attribute_completion(prop.set_attribute()) == 1:
                if isinstance(prop, ColoredProperty):
                    value += self.houses_on_set(prop.set_attribute() * prop.house_cost())
                value *= 4
            elif self.attribute_completion(prop.set_attribute()) >= 0.66:
                value *= 3
            elif self.attribute_completion(prop.set_attribute()) >= 0.5:
                value *= 2
            else:
                value *= 1.5
            values[prop.name] = value

        return values

    def attribute_completion(self, attr):
        count = 0
        total = 0

        for prop in self.client.properties:
            if attr in prop.attributes:
                count += 1

        for tile in self.client.game.board:
            if attr in tile.attributes:
                total += 1

        return count / total if total != 0 else 0

    def attribute_completions(self):
        out = {}
        for prop in self.client.properties:
            out[prop.set_attribute()] = self.attribute_completion(prop.set_attribute())
        return out

    def houses_on_set(self, set_attr):
        count = 0
        for prop in self.client.properties:
            if isinstance(prop, ColoredProperty) and set_attr in prop.attributes:
                count += prop.houses
        return count

    def most_wanted_set(self):
        completions = self.attribute_completions()
        largest = None

        for prop in self.client.properties:
            if largest is None:
                largest = prop.set_attribute()
            if completions[prop.set_attribute] > completions[largest]:
                largest = prop.set_attribute()
        return largest

    def best_trader_match(self):
        players = self.client.game.players
        best = players[0]
        most_wanted_set = self.most_wanted_set()  # Attribute

        for player in players:
            if self.count_properties_with_attribute(player, most_wanted_set) > self.count_properties_with_attribute(
                    best,
                    most_wanted_set):
                best = player
        return best


class TradeDeal:
    def __init__(self, p1, p2):
        self.player1 = p1
        self.player2 = p2
        self.player1acquisitions = []
        self.player2acquisitions = []
        self.compensation = 0

    def execute(self):
        if self.compensation > 0:
            pass  # TODO: fill this
        elif self.compensation < 0:
            pass  # TODO: fill this

        for prop in self.player1acquisitions:
            prop.transfer_ownership(self.player1)

        for prop in self.player2acquisitions:
            prop.transfer_ownership(self.player2)

        self.player1.add_money(-self.compensation)
        self.player2.add_money(self.compensation)


class TradeManager:
    @staticmethod
    def run_best_trade(client):
        broker = TradeBroker(client)
        other_player = broker.best_trader_match()
        other_broker = TradeBroker(client)
        deal = TradeDeal(client, other_player)
        receiving = broker.most_wanted_set()
        giving = other_broker.most_wanted_set()

        for prop in other_player.properties:
            if receiving in prop.attributes:
                deal.player1acquisitions.append(prop)

        for prop in client.properties:
            if giving in prop.attributes:
                deal.player2acquisitions.append(prop)

        player1value = 0
        player2value = 0

        values = broker.assign_property_values()
        for prop in deal.player2acquisitions:
            player1value += values[prop]

        values = other_broker.assign_property_values()
        for prop in deal.player1acquisitions:
            player2value += values[prop]

        deal.execute()
