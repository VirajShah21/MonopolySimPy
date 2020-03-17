from org.virajshah.monopoly.core import MonopolyGame, Player

if __name__ == "__main__":
    game: MonopolyGame = MonopolyGame()

    game.add_player(Player("Player 1", game))
    game.add_player(Player("Player 2", game))
    game.add_player(Player("Player 3", game))
    game.add_player(Player("Player 4", game))

    while len(game.players) > 1:
        game.run_next_turn()
