from typing import Dict, Tuple, List, Set

from competitive_sudoku.sudoku import GameState
from team27_A2.helpers import get_block_top_left_coordinates

import random


def remove_squares_with_many_options(moves_under_consideration: Dict[Tuple[int, int], List[int]],
                                     number_of_options: int):
    """
    TODO: might end up deleting this. If it's staying, write docs.
    """
    keys = moves_under_consideration.keys()
    keys_to_remove = []
    deleted = 0

    for key in keys:
        if len(moves_under_consideration[key]) >= number_of_options:
            deleted += 1
            keys_to_remove.append(key)

    for i in range(len(keys_to_remove)):
        moves_under_consideration.pop(keys_to_remove[i])

    return moves_under_consideration


def force_highest_points_moves(game_state: GameState,
                               moves_under_consideration: Dict[Tuple[int, int], List[int]],
                               allowed_in_rows: List[Set[int]],
                               allowed_in_columns: List[Set[int]],
                               allowed_in_blocks: Dict[Tuple[int, int], List[int]]):
    """
    Check the moves that are currently under consideration, and if there are moves
    in there that generate the most points possible (7 points) select only those moves
    and play one of those (since it can't get better than that).
    @param game_state: Current GameState that the moves are under consideration on.
    @param moves_under_consideration: A dict of (row,column):[values] describing which moves should be considered.
    @param allowed_in_rows: A list (size N) of sets, representing the allowed numbers in each row
    @param allowed_in_columns: A list (size N) of sets, representing the allowed numbers in each column
    @param allowed_in_blocks: A dictionary of coordinates as keys (top left square of a block),
                              with a set of the allowed numbers in the respective block as the value.
    @return: A dict of (row,column):[values] describing which moves should be considered.
    """
    forced_squares = []
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if (i, j) in moves_under_consideration:
                row_allowed = list(allowed_in_rows[i])
                column_allowed = list(allowed_in_columns[j])
                block_allowed = list(allowed_in_blocks[
                                         get_block_top_left_coordinates(
                                             i, j, game_state.board.m, game_state.board.n)])

                # If there is exactly one value possible in the row, column and block and their values
                #   are all the same, this value in this spot would give 7 points and this is a
                #   valuable move for sure.
                if len(row_allowed) == 1 and len(column_allowed) == 1 and len(block_allowed) == 1:
                    if row_allowed[0] == column_allowed[0] and row_allowed[0] == block_allowed[0]:
                        forced_squares.append((i, j))

    if len(forced_squares) > 0:
        # If there are 7 point value moves under consideration, return only those.
        forced_moves = {}
        for square in forced_squares:
            forced_moves[square] = moves_under_consideration[square]
        return forced_moves
    else:
        # Otherwise, return the original dictionary of moves.
        return moves_under_consideration


def remove_moves_that_allows_opponent_to_score(game_state: GameState,
                                               moves_under_consideration: Dict[Tuple[int, int], List[int]],
                                               allowed_in_rows: List[Set[int]],
                                               allowed_in_columns: List[Set[int]],
                                               allowed_in_blocks: Dict[Tuple[int, int], List[int]]):
    """
    Removes moves (in early game) that allow the opponent to easily score points
    """
    to_remove = []

    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if (i, j) in moves_under_consideration:
                row_allowed = allowed_in_rows[i]
                column_allowed = allowed_in_columns[j]
                block_allowed = allowed_in_blocks[
                    get_block_top_left_coordinates(i, j, game_state.board.m, game_state.board.n)]

                amount_allowed_in_row = len(row_allowed)
                amount_allowed_in_column = len(column_allowed)
                amount_allowed_in_block = len(block_allowed)

                opponent_can_finish_if_filled = False
                opponent_can_finish_if_filled = True if amount_allowed_in_row == 2 else opponent_can_finish_if_filled
                opponent_can_finish_if_filled = True if amount_allowed_in_column == 2 else opponent_can_finish_if_filled
                opponent_can_finish_if_filled = True if amount_allowed_in_block == 2 else opponent_can_finish_if_filled

                can_score_points = False
                if amount_allowed_in_row == 1 or amount_allowed_in_block == 1 or amount_allowed_in_column == 1:
                    can_score_points = True

                above_3_missing = 0
                above_3_missing += 1 if len(row_allowed) > 3 else 0
                above_3_missing += 1 if len(column_allowed) > 3 else 0
                above_3_missing += 1 if len(block_allowed) > 3 else 0

                if opponent_can_finish_if_filled or (above_3_missing >= 2 and not can_score_points):
                    to_remove.append((i, j))

    # if len(moves_under_consideration.keys()) - len(to_remove) <= 7:
    #     to_remove = random.sample(to_remove, max(0, len(moves_under_consideration) - 7))

    if len(moves_under_consideration.keys()) - len(to_remove) > 7:
        for i in range(len(to_remove)):
            moves_under_consideration.pop(to_remove[i])

    return moves_under_consideration


def one_move_per_square(moves_under_consideration: Dict[Tuple[int, int], List[int]]):
    """
    If there are still squares with more than one option, we don't want to guess, and thus better just remove all
    options of those squares.
    """
    to_remove = []
    for key in moves_under_consideration.keys():
        moves = moves_under_consideration[key]
        if len(moves) > 1:
            to_remove.append(key)

    if len(moves_under_consideration.keys()) - len(to_remove) > 7:
        for key in to_remove:
            moves_under_consideration.pop(key)
    return moves_under_consideration
