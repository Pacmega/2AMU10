#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
from typing import Set, List

from competitive_sudoku.sudoku import GameState, Move
import competitive_sudoku.sudokuai
from copy import deepcopy


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration. This particular
    implementation is the agent of group 27 for Foundations of AI.
    """

    def __init__(self):
        """
        Create a new SudokuAI agent, using nothing particular that was not
        already present in the original implementation this agent inherits
        its basic capabilities from.
        """
        super().__init__()

    def compute_all_legal_moves(self, game_state: GameState) -> List[Move]:
        """
        Computes all the possible moves in the game state,
        minus the taboo moves specified by the GameState.
        @param game_state: The GameState to compute all legal moves for.
        @return: A list of Moves, with each individual move being a legal one for
            the given GameState
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

        # Consequently, loop over each of the empty squares and take the
        # intersection of allowed moves for the row, column and block for that square
        allowed_moves = {}
        for i in range(game_state.board.N):
            for j in range(game_state.board.N):
                if game_state.board.get(i, j) == game_state.board.empty:
                    allowed_moves[(i, j)] = rows[i] \
                        .intersection(columns[j]) \
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
        Finds the numbers that are still allowed to be placed in the block that
        cell [row,column] is in on the board in the given GameState.
        @param game_state: The GameState containing the board that cell [row,int]
            should be checked on.
        @param row: An integer describing the row that the cell [row,column] is in.
        @param column: An integer describing the column that the cell [row,column] is in.
        @return: A set containing all numbers that are not yet present in the block.
        """
        numbers_in_block = set(())

        # Determine the exact start and end of the block that this cell
        #   is in with the help of the available board size parameters
        # Note that there is no requirement for square blocks in this sudoku
        block_start_row = row - (row % game_state.board.m)
        block_end_row = row + (game_state.board.m - (row % game_state.board.m))
        block_start_column = column - (column % game_state.board.n)
        block_end_column = column + (game_state.board.n - (column % game_state.board.n))

        # Iterate over all cells in the block, and add their values to the set
        # Note that these values are necessarily distinct by the rules of sudoku
        for i in range(block_start_row, block_end_row):
            for j in range(block_start_column, block_end_column):
                value = game_state.board.get(i, j)
                if value is not game_state.board.empty:
                    numbers_in_block.add(value)

        # Finally take all possible numbers, and strike from those the
        #   ones that already appear. This gives all remaining numbers.
        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_block)

    def allowed_numbers_in_row(self, game_state: GameState, row: int) -> Set[int]:
        """
        Finds the numbers that are still allowed to be placed in
        the given row on the board in the given GameState.
        @param game_state: The GameState containing the board that this row
            should be checked on.
        @param row: An integer describing the row to check.
        @return: A set containing all numbers that are not yet present in the row.
        """
        numbers_in_row = set(())

        # Iterate over all cells in the given row, and add their values to the set
        # Note that these values are necessarily distinct by the rules of sudoku
        for column in range(game_state.board.N):
            value = game_state.board.get(row, column)
            if value is not game_state.board.empty:
                numbers_in_row.add(value)

        # Finally take all possible numbers, and strike from those the
        #   ones that already appear. This gives all remaining numbers.
        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_row)

    def allowed_numbers_in_column(self, game_state: GameState, column: int) -> Set[int]:
        """
        Finds the numbers that are still allowed to be placed in
        the given column on the board in the given GameState.
        @param game_state: The GameState containing the board that this column
            should be checked on.
        @param column: An integer describing the column to check.
        @return: A set containing all numbers that are not yet present in the column.
        """
        numbers_in_column = set(())

        # Iterate over all cells in the given column, and add their values to the set
        # Note that these values are necessarily distinct by the rules of sudoku
        for row in range(game_state.board.N):
            value = game_state.board.get(row, column)
            if value is not game_state.board.empty:
                numbers_in_column.add(value)

        all_numbers = set((range(1, game_state.board.N + 1)))
        return all_numbers.difference(numbers_in_column)

    def compute_best_move(self, game_state: GameState) -> None:
        """
        Main agent function to call. This function iteratively explores the
        possible moves and future states of the game via a minimax algorithm
        including A-B pruning, and continues to search further for as long as
        it is allowed. This function does not terminate in normal execution.
        @param game_state: The current GameState that the next move should be
            computed for.
        @return: Nothing. (function should not terminate in normal execution)
        """
        i = 1

        # Suggest a random legal move at first to make sure we always have something
        self.propose_move(random.choice(self.compute_all_legal_moves(game_state)))

        while True:
            if self.board_filled_in(game_state):
                break
                
            # Which player we are can be deduced from the number of previous
            #   moves, and from that we can tell whether we want to maximize
            #   or minimize our evaluation function (score P1 - score P2)
            maximizing_player = not bool(len(game_state.moves) % 2)

            value, optimal_move = self.minimax(game_state, i, maximizing_player, -100000, 100000)
            if optimal_move is None:
                break
            else:
                self.propose_move(optimal_move)
            i += 1

    def board_filled_in(self, game_state: GameState) -> bool:
        """Helper function to check if there are any empty cells on the board."""
        for i in range(game_state.board.N):
            for j in range(game_state.board.N):
                if game_state.board.get(i, j) == game_state.board.empty:
                    return False
        return True

    def minimax(self, game_state: GameState, depth: int, maximizing_player: bool, alpha: int, beta: int) -> (int, Move):
        """
        The minimax algorithm used by this agent to find the best move possible,
        also using Alpha-Beta pruning in order to stops evaluating a move sooner
        when at least one possibility has been found that proves the move to be
        worse than a previously examined move.
        @param game_state: The current GameState that the next move should be computed for.
        @param depth: The maximum amount of levels that the game tree should be explored up to.
        @param maximizing_player: Boolean specifying whether the current player being evaluated is
            the one that wants to maximize the evaluation heuristic (Player 1).
        @param alpha: The minimum score that the maximizing player is assured of
        @param beta: The maximum score that the minimizing player is assured of
        @return: A tuple specifying the value of this move for this player, and the corresponding move.
        """
        if depth == 0 or self.board_filled_in(game_state):
            return self.evaluate(game_state), None

        if maximizing_player:
            value = -100000
            best_move = None
            for move in self.compute_all_legal_moves(game_state):
                # Simulate a possible move, and recursively call minimax again
                #   to explore further down the tree how this move plays out.
                new_game_state = self.simulate_move(game_state, move)
                new_value, new_move = self.minimax(new_game_state, depth-1, False, alpha, beta)

                if new_value > value:
                    best_move = move
                    value = new_value

                if value >= beta:
                    break

                alpha = max(alpha, value)
            return value, best_move

        else:
            value = 1000000
            best_move = None
            for move in self.compute_all_legal_moves(game_state):
                # Simulate a possible move, and recursively call minimax again
                #   to explore further down the tree how this move plays out.
                new_game_state = self.simulate_move(game_state, move)
                new_value, new_move = self.minimax(new_game_state, depth-1, True, alpha, beta)

                if new_value < value:
                    best_move = move
                    value = new_value

                if value <= alpha:
                    break

                beta = max(beta, value)
            return value, best_move

    def simulate_move(self, game_state: GameState, move: Move) -> GameState:
        """
        Simulates the execution of the given Move on the given GameState. This function
        does not check whether a move might be taboo, and instead just executes it.
        The function internally deduces from the length of game_state.moves
        for which player the given move should be played.
        @param game_state: The GameState to execute/simulate the given move on.
        @param move: The move to execute/simulate on the given GameState.
        @return: The new GameState after this move is performed.
                   Scores, moves and board are updated.
        """
        score = 0
        regions_completed = 0

        # The player we are simulating for, either P1 or P2, can be deduced
        #   from the length of the move history (player 1 always goes first)

        simulating_for = len(game_state.moves) % 2

        # We create a deep copy of the given game_state, so that we are sure
        #   that we do not unintentionally modify the true game state.
        future_state = deepcopy(game_state)
        future_state.board.put(move.i, move.j, move.value)
        future_state.moves.append(move)

        # Play the passed move on the board and see how many points
        #   would be earned. The amount of points scored for a move
        #   depends on the amount of regions completed with that move.
        #   At most, a move could simultaneously complete a row,
        #   a column and a block, giving 7 points at once.
        block_values_left = len(self.allowed_numbers_in_block(future_state,
                                                              move.i,
                                                              move.j))
        row_values_left = len(self.allowed_numbers_in_row(future_state,
                                                          move.i))
        col_values_left = len(self.allowed_numbers_in_column(future_state,
                                                             move.j))

        if block_values_left == 0:
            regions_completed += 1
        if row_values_left == 0:
            regions_completed += 1
        if col_values_left == 0:
            regions_completed += 1

        if regions_completed == 1:
            score = 1
        elif regions_completed == 2:
            score = 3
        elif regions_completed == 3:
            score = 7

        if simulating_for == 0:
            future_state.scores[0] += score
        else:
            future_state.scores[1] += score

        return future_state

    def evaluate(self, game_state: GameState):
        """
        Calculate the heuristic that is used by the minimax algorithm
        to see which moves and options are good for either player.
        Calculation used: Player 1's score - Player 2's score
        """
        return game_state.scores[0] - game_state.scores[1]
