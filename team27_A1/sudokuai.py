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

    def get_used_row_col_values(self, game_state: GameState, move: Move):
        values_found = []

        for it in range(game_state.board.N):
            row_part = game_state.board.get(it, move.j)
            col_part = game_state.board.get(move.i, it)

            if row_part not in values_found:
                values_found.append(row_part)
            if col_part not in values_found:
                values_found.append(col_part)

        return values_found

    def get_used_block_values(self, game_state: GameState, move: Move):
        values_found = []

        block_rows = game_state.board.m
        block_cols = game_state.board.n
        # Truncation to integer == floor but with type casting included
        vertical_block = int(move.i / block_rows)
        horizontal_block = int(move.j / block_cols)

        for i in range(block_cols):
            for j in range(block_rows):
                cell_value = game_state.board.get(vertical_block*block_rows + j,
                                                  horizontal_block*block_cols + i)
                if cell_value not in values_found:
                    values_found.append(cell_value)

        return values_found

    def generate_legal_moves(self, game_state: GameState):
        # Not just possible, actually legal

        N = game_state.board.N

        possible_moves = [Move(i, j, -1) for i in range(N) \
                                         for j in range(N) \
                              if game_state.board.get(i, j) == SudokuBoard.empty]

        legal_moves = []

        for move in possible_moves:
            # Check for this cell which values already appear in
            #   its row, column and block
            values_in_row_col = self.get_used_row_col_values(game_state, move)
            values_in_block = self.get_used_block_values(game_state, move)

            for value in range(1, N+1):
                if not (TabooMove(move.i, move.j, value) in game_state.taboo_moves or \
                        value in values_in_block or value in values_in_row_col):
                    legal_moves.append(Move(move.i, move.j, value))

        return legal_moves

    def compute_best_move(self, game_state: GameState) -> None:
        legal_moves = self.generate_legal_moves(game_state)
        # print('moves generated')
        move = random.choice(legal_moves)

        self.propose_move(move)
        while True:
            time.sleep(0.2)
            self.propose_move(random.choice(legal_moves))

    def minimax(self, game_state: GameState, depth: int, maximizing_player: int):
        pass

    def eval_function(self, game_state: GameState, move: Move):
        pass