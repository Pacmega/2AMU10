#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)
import itertools
import random
from typing import Dict, List, Set

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    # N.B. This is a very naive implementation.
    def compute_best_move(self, game_state: GameState) -> None:
        all_moves = self.compute_all_possible_moves(game_state)
        all_empty_squares = list(all_moves.keys())
        square = random.choice(all_empty_squares)
        moves_of_square = list(all_moves[square])
        val = random.choice(moves_of_square)
        self.propose_move(Move(square[0], square[1], val))

    def compute_all_possible_moves(self, game_state: GameState) -> Dict[tuple, Set[int]]:
        """
        Computes all the possible moves in the game state, minus the taboo moves specified by the GameState
        """

        # First get all allowed numbers for each of the rows and columns
        rows = {}
        columns = {}
        for i in range(game_state.board.N):
            rows[i] = self.allowed_numbers_in_row(game_state, i)
            columns[i] = self.allowed_numbers_in_column(game_state, i)

        # Next, get all allowed numbers for each of the blocks
        blocks = {}
        horizontal_dividers = range(0, game_state.board.N, game_state.board.n)
        vertical_dividers = range(0, game_state.board.N, game_state.board.m)
        all_combinations = []
        for i in vertical_dividers:
            for j in horizontal_dividers:
                all_combinations.append((i, j))

        for block_index in all_combinations:
            blocks[block_index] = self.allowed_numbers_in_block(game_state, block_index[0], block_index[1])

        # Consequently, loop over each of the empty squares;
        # take the intersection of allowed moves for the row, column and block
        allowed_moves = {}
        for i in range(game_state.board.N):
            for j in range(game_state.board.N):
                if game_state.board.get(i, j) == game_state.board.empty:
                    row_allowed = rows[i]
                    column_allowed = columns[j]
                    blocks_allowed = blocks[(i - (i % game_state.board.m), j - (j % game_state.board.n))]

                    allowed = row_allowed.intersection(column_allowed).intersection(blocks_allowed)
                    allowed_moves[(i, j)] = allowed

        # Lastly, remove all taboo moves
        for taboo_move in game_state.taboo_moves:
            if (taboo_move.i, taboo_move.j) in list(allowed_moves.keys()):
                square_moves = allowed_moves[(taboo_move.i, taboo_move.j)]
                if taboo_move.value in square_moves:
                    allowed_moves.get((taboo_move.i, taboo_move.j)).remove(taboo_move.value)

        return allowed_moves

    def allowed_numbers_in_block(self, game_state: GameState, row: int, column: int) -> Set[int]:
        """
        Calculates the allowed numbers to be placed in the block, given the game state and any row and column.
        Does not check whether row and column are in the board parameters.
        """
        numbers_in_block = set(())
        for i in range(row - (row % game_state.board.m), row + (game_state.board.m - (row % game_state.board.m))):
            for j in range(column - (column % game_state.board.n),
                           column + (game_state.board.n - (column % game_state.board.n))):
                value = game_state.board.get(i, j)
                if value is not game_state.board.empty:
                    numbers_in_block.add(value)

        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_block)

    def allowed_numbers_in_row(self, game_state: GameState, row: int) -> Set[int]:
        """
        Calculates the allowed numbers to be placed in the row, given the game state and any row index.
        Does not check whether row is in the board parameters.
        """
        numbers_in_row = set(())
        for column in range(game_state.board.N):
            value = game_state.board.get(row, column)
            if value is not game_state.board.empty:
                numbers_in_row.add(value)

        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_row)

    def allowed_numbers_in_column(self, game_state: GameState, column: int):
        """
        Calculates the allowed numbers to be placed in the column, given the game state and any column index.
        Does not check whether column is in the board parameters.
        """
        numbers_in_column = set(())
        for row in range(game_state.board.N):
            value = game_state.board.get(row, column)
            if value is not game_state.board.empty:
                numbers_in_column.add(value)

        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_column)
