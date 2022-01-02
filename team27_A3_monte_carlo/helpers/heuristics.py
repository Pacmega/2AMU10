import random
from typing import Dict, Tuple, List, Set

from competitive_sudoku.sudoku import GameState
from team27_A3.helpers import get_block_top_left_coordinates


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
    for cell in moves_under_consideration:
        row_index = cell[0]
        column_index = cell[1]

        row_allowed = list(allowed_in_rows[row_index])
        column_allowed = list(allowed_in_columns[column_index])
        block_allowed = list(allowed_in_blocks[
                                 get_block_top_left_coordinates(
                                     row_index, column_index, game_state.board.m, game_state.board.n)])

        # If there is exactly one value possible in the row, column and block and their values
        #   are all the same, this value in this spot would give 7 points and this is a
        #   valuable move for sure.
        if len(row_allowed) == 1 and len(column_allowed) == 1 and len(block_allowed) == 1:
            if row_allowed[0] == column_allowed[0] and row_allowed[0] == block_allowed[0]:
                forced_squares.append(cell)

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
    This function calculates several combined heuristics (to save computational time).
    It loops over each empty square, and checks whether
        1. If filled in, can the opponent then score points. If so, do not consider the move.
        2. Do 2 or more of respective row, column or block have more than 3 open squares left. If so, this move is so
            far away from useful that we should not consider it.
    @param game_state: Current GameState that the moves are under consideration on.
    @param moves_under_consideration: A dict of (row,column):[values] describing which moves should be considered.
    @param allowed_in_rows: A list (size N) of sets, representing the allowed numbers in each row
    @param allowed_in_columns: A list (size N) of sets, representing the allowed numbers in each column
    @param allowed_in_blocks: A dictionary of coordinates as keys (top left square of a block),
                              with a set of the allowed numbers in the respective block as the value.
    @return: Two items:
             1. A dict of (row,column):[values] describing which moves should be considered.
             2. A boolean denoting whether the player (or rather, the Node) calling the function could score right now.
    """
    to_remove = []
    can_score_overall = False

    for cell in moves_under_consideration:
        row_index = cell[0]
        column_index = cell[1]

        row_allowed = allowed_in_rows[row_index]
        column_allowed = allowed_in_columns[column_index]
        block_allowed = allowed_in_blocks[
            get_block_top_left_coordinates(row_index, column_index, game_state.board.m, game_state.board.n)]

        amount_allowed_in_row = len(row_allowed)
        amount_allowed_in_column = len(column_allowed)
        amount_allowed_in_block = len(block_allowed)

        opponent_can_finish_if_filled = False
        opponent_can_finish_if_filled = True if amount_allowed_in_row == 2 else opponent_can_finish_if_filled
        opponent_can_finish_if_filled = True if amount_allowed_in_column == 2 else opponent_can_finish_if_filled
        opponent_can_finish_if_filled = True if amount_allowed_in_block == 2 else opponent_can_finish_if_filled

        above_3_missing = 0
        above_3_missing += 1 if len(row_allowed) > 3 else 0
        above_3_missing += 1 if len(column_allowed) > 3 else 0
        above_3_missing += 1 if len(block_allowed) > 3 else 0

        can_score = len(row_allowed) == 1 or len(column_allowed) == 1 or len(block_allowed) == 1
        can_score_overall = can_score or can_score_overall

        if (opponent_can_finish_if_filled or above_3_missing >= 2) and not can_score:
            to_remove.append(cell)

    # Ensure that we don't remove so much that there is basically nothing left to play anymore, before removing it
    threshold = 5
    if len(moves_under_consideration) - len(to_remove) > threshold:
        for i in range(len(to_remove)):
            moves_under_consideration.pop(to_remove[i])
    else:
        subset = random.sample(to_remove,
                               max(len(moves_under_consideration) - threshold, 0))
        for i in range(len(subset)):
            moves_under_consideration.pop(to_remove[i])

    return moves_under_consideration, can_score_overall


def one_move_per_square(moves_under_consideration: Dict[Tuple[int, int], List[int]]):
    """
    If there are still squares with more than one option, we want to minimize guessing and
    minimax computation time so we decide to just remove all options of those squares.
    If that means that we have less than 7 potential squares left, they are not removed.
    @param moves_under_consideration: A dict of (row,column):[values] describing which moves should be considered.
    @return:                          None, moves_under_consideration is edited in-place.
    """
    to_remove = []
    for key in moves_under_consideration:
        moves = moves_under_consideration[key]
        if len(moves) > 1:
            to_remove.append(key)

    threshold = 5
    if len(moves_under_consideration) - len(to_remove) > threshold:
        # If this process would cut the options down too far, we don't want to remove.
        for key in to_remove:
            moves_under_consideration.pop(key)
    else:
        subset = random.sample(to_remove,
                               max(len(moves_under_consideration) - threshold, 0))
        for i in range(len(subset)):
            moves_under_consideration.pop(subset[i])

    return
