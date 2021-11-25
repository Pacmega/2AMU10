#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
from typing import Set, List

from competitive_sudoku.sudoku import GameState, Move
import competitive_sudoku.sudokuai


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def compute_all_legal_moves(self, game_state: GameState) -> List[Move]:
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
        all_block_indices = [(i, j)
                             for i in range(0, game_state.board.N, game_state.board.m)
                             for j in range(0, game_state.board.N, game_state.board.n)]

        blocks = {}
        for block_index in all_block_indices:
            blocks[block_index] = self.allowed_numbers_in_block(game_state, block_index[0], block_index[1])

        # Consequently, loop over each of the empty squares;
        # take the intersection of allowed moves for the row, column and block
        allowed_moves = {}
        for i in range(game_state.board.N):
            for j in range(game_state.board.N):
                if game_state.board.get(i, j) == game_state.board.empty:
                    allowed_moves[(i, j)] = rows[i]\
                        .intersection(columns[j])\
                        .intersection(blocks[(i - (i % game_state.board.m), j - (j % game_state.board.n))])

        all_empty_squares = allowed_moves.keys()

        # Lastly, remove all taboo moves
        for taboo_move in game_state.taboo_moves:
            if (taboo_move.i, taboo_move.j) in list(all_empty_squares):
                square_moves = allowed_moves[(taboo_move.i, taboo_move.j)]
                if taboo_move.value in square_moves:
                    allowed_moves.get((taboo_move.i, taboo_move.j)).remove(taboo_move.value)

        # Write everything to a list
        moves_list = []
        for square in all_empty_squares:
            moves = allowed_moves[square]
            for move in moves:
                moves_list.append(Move(square[0], square[1], move))

        return moves_list

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

    def allowed_numbers_in_column(self, game_state: GameState, column: int) -> Set[int]:
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

    def compute_best_move(self, game_state: GameState) -> None:
        legal_moves = self.compute_all_legal_moves(game_state)
        move = random.choice(legal_moves)

        self.propose_move(move)
        while True:
            time.sleep(0.2)
            self.propose_move(random.choice(legal_moves))

    def minimax(self, game_state: GameState, depth: int, maximizing_player: int):
        pass

    def eval_function(self, game_state: GameState, move: Move):
        pass
