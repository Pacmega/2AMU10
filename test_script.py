import importlib
import platform
from pathlib import Path
import csv

from competitive_sudoku.sudoku import load_sudoku_from_text
from simulate_game import simulate_game


def main():
    solve_sudoku_path = 'bin\\solve_sudoku.exe' if platform.system() == 'Windows' else 'bin/solve_sudoku'

    ###
    # Variables you might want to set specifically
    ###
    times_to_test = [0.5, 1]

    player_configs_to_test = [("team27_A2", "greedy_player"),
                              ("greedy_player", "team27_A2")]

    boards_to_tests = ["boards/easy-2x2.txt"]

    runs_per_config = 5

    for time in times_to_test:
        for player_config in player_configs_to_test:
            for board_path in boards_to_tests:
                # stores [#draws, #wins_player1, #wins_player2]
                results_for_config = [0, 0, 0]
                scores = []

                for i in range(runs_per_config):
                    board_text = Path(board_path).read_text()
                    board = load_sudoku_from_text(board_text)

                    bot_1 = player_config[0]
                    bot_2 = player_config[1]

                    module1 = importlib.import_module(bot_1 + '.sudokuai')
                    module2 = importlib.import_module(bot_2 + '.sudokuai')
                    player1 = module1.SudokuAI()
                    player2 = module2.SudokuAI()
                    if bot_1 in ('random_player', 'greedy_player'):
                        player1.solve_sudoku_path = solve_sudoku_path
                    if bot_2 in ('random_player', 'greedy_player'):
                        player2.solve_sudoku_path = solve_sudoku_path

                    scores, won = simulate_game(board, player1, player2, solve_sudoku_path=solve_sudoku_path,
                                                calculation_time=time)
                    print("final score: " + str(scores[0]) + " - " + str(scores[1]) + ". Player " + str(won) + " won")
                    results_for_config[won] += 1
                    scores.append(scores)

                print("===========================================================")
                print("Final results for config:")
                print("Time: " + str(time))
                print("Board: " + str(board_path))
                print("Player 1: " + str(player_config[0]) + " won " + str(results_for_config[1]) + " game(s)")
                print("Player 2: " + str(player_config[1]) + " won " + str(results_for_config[2]) + " game(s)")
                print(str(results_for_config[0]) + " game(s) was/were drawn")

                with open('results.csv', 'a') as fd:
                    line = [str(time), str(runs_per_config), board_path, player_config[0], player_config[1],
                            str(results_for_config[0]), str(results_for_config[1]), str(results_for_config[2])]
                    write = csv.writer(fd)
                    write.writerow(line)


if __name__ == '__main__':
    main()