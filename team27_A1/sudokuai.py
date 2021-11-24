#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def get_used_row_or_col_values(self, game_state: GameState, index, get_col):
        values_found = []

        for i in range(game_state.board.N):
            if get_col:
                # Get values occurring in column, iterate over rows
                cell_value = game_state.board.get(i, index)
            else:
                # Get values occurring in row, iterate over columns
                cell_value = game_state.board.get(index, i)

            if cell_value not in values_found:
                values_found.append(cell_value)

        return values_found

    def get_used_block_values(self, game_state: GameState, i, j):
        # TODO: any easy way to determine which block (i, j) is in?
        # TODO: actually implement this
        values_found = []

        raise NotImplementedError()

        return values_found

    def generate_legal_moves(self, game_state: GameState):
        # Note to self: not just possible, actually legal
        # TODO: implement this

        possible_moves = [Move(i, j, -1) for i in range(N) \
                                         for j in range(N) \
                              if game_state.board.get(i, j) == SudokuBoard.empty]

        legal_moves = []

        for move in possible_moves:
            for value in range(1, N+1):
                print("AAAAA")

        raise NotImplementedError()

    # N.B. This is a very naive implementation.
    def compute_best_move(self, game_state: GameState) -> None:
        # Get total board size (doubles as highest possible value)
        N = game_state.board.N

        def possible(i, j, value):
            # TODO: this does not check legality, only if the square is non-empty
            return game_state.board.get(i, j) == SudokuBoard.empty and not TabooMove(i, j, value) in game_state.taboo_moves



        print(game_state.board.get(game_state.board.m-1,game_state.board.n-1))
        print(game_state.board.get(N-1,N-1))
        print(N)
        all_moves = [Move(i, j, -1) for i in range(N) \
                                       for j in range(N) \
                                       for value in range(1, N+1) \
                     if possible(i, j, value)]
        move = random.choice(all_moves)
        self.propose_move(move)
        while True:
            time.sleep(0.2)
            self.propose_move(random.choice(all_moves))
