from typing import Dict, Tuple, List, Set

from competitive_sudoku.sudoku import GameState
from team27_A2.helpers import get_block_top_left_coordinates


def remove_squares_with_many_options(moves_under_consideration: Dict[Tuple[int, int], List[int]],
                                     number_of_options: int):
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
    forced_squares = []
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if (i, j) in moves_under_consideration:
                row_allowed = list(allowed_in_rows[i])
                column_allowed = list(allowed_in_columns[j])
                block_allowed = list(allowed_in_blocks[get_block_top_left_coordinates(i, j, game_state.board.m, game_state.board.n)])

                if len(row_allowed) == 1 and len(column_allowed) == 1 and len(block_allowed) == 1:
                    if row_allowed[0] == column_allowed[0] and row_allowed[0] == block_allowed[0]:
                        forced_squares.append((i, j))

    if len(forced_squares) > 0:
        forced_moves = {}
        for square in forced_squares:
            forced_moves[square] = moves_under_consideration[square]
        return forced_moves
    else:
        return moves_under_consideration
