from copy import deepcopy
from typing import List, Set, Dict, Tuple

from competitive_sudoku.sudoku import GameState, Move, TabooMove, SudokuBoard
import time
import numpy as np

"""
This file contains functions that extend the functionality of the GameState class, such as calculating 
acceptable moves, checking whether the board still contains an empty square, or simulating a move on a GameState object.
"""


def board_filled_in(game_state: GameState) -> bool:
    """
    Helper function to check if there are any empty cells on the board.
    @param game_state: The GameState for which to check if the board is full.
    @return: Boolean stating whether the board is 100% full or not.
    """
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if game_state.board.get(i, j) == game_state.board.empty:
                return False
    return True


def board_half_filled_in(game_state: GameState) -> bool:
    """
    Helper function to check if the board has been filled for >= 50%.
    @param game_state: The GameState for which to check if the board is >= 50% full.
    @return: Boolean stating whether the board is >= 50% full or not.
    """
    cells_filled_in = 0
    total_cells = game_state.board.N * game_state.board.N

    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if game_state.board.get(i, j) != game_state.board.empty:
                cells_filled_in += 1

    fraction_filled_in = cells_filled_in / total_cells

    if fraction_filled_in >= 0.5:
        return True
    else:
        return False


def compute_all_legal_moves(game_state: GameState) \
        -> (Dict[Tuple[int, int], List[int]], List[Set[int]], List[Set[int]], Dict[Tuple[int, int], List[int]]):
    """
    Computes all the possible moves in the game state,
    minus the taboo moves specified by the GameState.
    @param game_state:  The GameState to compute all legal moves for.
    @return:            A tuple with 4 values:
                            (1) A dictionary with coordinates as keys, and lists of legal values for the respective
                                square as values.
                            (2) A list (size N) of sets, representing the allowed numbers in each row
                            (3) A list (size N) of sets, representing the allowed numbers in each column
                            (4) A dictionary of coordinates as keys (top left square of a block),
                                with a set of the allowed numbers in the respective block as the value.
    """
    in_row = [set(()) for i in range(game_state.board.N)]
    in_column = [set(()) for j in range(game_state.board.N)]

    all_block_indices = [(i, j)
                         for i in range(0, game_state.board.N, game_state.board.m)
                         for j in range(0, game_state.board.N, game_state.board.n)]
    in_block: Dict[Tuple[int, int], Set] = {}
    for index in all_block_indices:
        in_block[index] = set(())

    allowed_in_cell = {}

    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            cell = game_state.board.get(i, j)
            if cell is not game_state.board.empty:
                in_row[i].add(cell)
                in_column[j].add(cell)

                block = get_block_top_left_coordinates(i, j, game_state.board.m, game_state.board.n)
                in_block[block].add(cell)
            else:
                allowed_in_cell[(i, j)] = set(())

    not_in_row = [
        set(range(1, game_state.board.N+1)).difference(in_row[i])
        for i in range(game_state.board.N)
    ]
    not_in_column = [
        set(range(1, game_state.board.N+1)).difference(in_column[i])
        for i in range(game_state.board.N)
    ]

    not_in_block = {}
    for key, value in in_block.items():
        not_in_block[key] = list(set(range(1, game_state.board.N+1)).difference(value))

    for row, column in allowed_in_cell:
        allowed_in_cell[(row, column)] = list(not_in_row[row].intersection(not_in_column[column])\
            .intersection(not_in_block[get_block_top_left_coordinates(row, column,
                                                                      game_state.board.m, game_state.board.n)]))

    # Lastly, remove all taboo moves
    for taboo_move in game_state.taboo_moves:
        if (taboo_move.i, taboo_move.j) in allowed_in_cell:
            square_moves = allowed_in_cell[(taboo_move.i, taboo_move.j)]
            if taboo_move.value in square_moves:
                allowed_in_cell.get((taboo_move.i, taboo_move.j)).remove(taboo_move.value)

    return allowed_in_cell, not_in_row, not_in_column, not_in_block


def allowed_numbers_in_block(game_state: GameState, row: int, column: int) -> Set[int]:
    """
    Finds the numbers that are still allowed to be placed in the block that
    cell [row,column] is in on the board in the given GameState.
    @param game_state:  The GameState containing the board that cell [row,int]
                            should be checked on.
    @param row:         An integer describing the row that the cell [row,column] is in.
    @param column:      An integer describing the column that the cell [row,column] is in.
    @return:            A set containing all numbers that are not yet present in the block.
    """
    numbers_in_block = set(())

    # Determine the exact start and end of the block that this cell
    #   is in with the help of the available board size parameters
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


def allowed_numbers_in_row(game_state: GameState, row: int) -> Set[int]:
    """
    Finds the numbers that are still allowed to be placed in
    the given row on the board in the given GameState.
    @param game_state:  The GameState containing the board that this row
                            should be checked on.
    @param row:         An integer describing the row to check.
    @return:            A set containing all numbers that are not yet present in the row.
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


def allowed_numbers_in_column(game_state: GameState, column: int) -> Set[int]:
    """
    Finds the numbers that are still allowed to be placed in
    the given column on the board in the given GameState.
    @param game_state:  The GameState containing the board that this column
                            should be checked on.
    @param column:      An integer describing the column to check.
    @return:            A set containing all numbers that are not yet present in the column.
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


def simulate_move(game_state: GameState, move: Move, taboo_move: bool) -> GameState:
    """
    Simulates the execution of the given Move on the given GameState. This function
    does not check whether a move might be taboo, and instead just executes it.
    The function internally deduces from the length of game_state.moves
    for which player the given move should be played.
    @param game_state:  The GameState to execute/simulate the given move on.
    @param move:        The move to execute/simulate on the given GameState.
    @param taboo_move:  Whether the move is a taboo move or not
    @return:            The new GameState after this move is performed.
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
    if taboo_move:
        future_state.moves.append(TabooMove(move.i, move.j, move.value))
        return future_state

    future_state.board.put(move.i, move.j, move.value)
    future_state.moves.append(move)

    # Play the passed move on the board and see how many points
    #   would be earned. The amount of points scored for a move
    #   depends on the amount of regions completed with that move.
    #   At most, a move could simultaneously complete a row,
    #   a column and a block, giving 7 points at once.
    block_values_left = len(allowed_numbers_in_block(future_state,
                                                     move.i,
                                                     move.j))
    row_values_left = len(allowed_numbers_in_row(future_state,
                                                 move.i))
    col_values_left = len(allowed_numbers_in_column(future_state,
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


def get_block_top_left_coordinates(row_index: int, column_index: int, m: int, n: int) -> Tuple[int, int]:
    """
    Small function to retrieve the top left coordinates of the block that a given cell is in.
    This coordinate can then be used to retrieve data from allowed_in_blocks.
    @param row_index:    The row coordinate of the cell to retrieve block coordinates for.
    @param column_index: The column coordinate of the cell to retrieve block coordinates for.
    @param m:            The number of rows per block (generally stored in game_state.board.m, hence the name).
    @param n:            The number of columns per block (generally stored in game_state.board.n, hence the name).
    @return:             A tuple of (row, column) coordinates specifying the top left coordinates of the block.
    """
    return row_index - (row_index % m), column_index - (column_index % n)


def even_number_of_squares_left(game_state: GameState) -> bool:
    """
    Function that scans the board of the given GameState to check if there is an even number
    of empty cells left on the board.
    @param game_state: The GameState whose board to check.
    @return:           A Boolean specifying whether
    """
    empty_squares = 0
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if game_state.board.get(i, j) is game_state.board.empty:
                empty_squares += 1
    if empty_squares % 2 == 0:
        return True
    return False


def empty_spaces_as_numpy_array(board: SudokuBoard) -> np.ndarray:
    new_board = np.zeros((board.N, board.N), dtype=int)
    for i in range(board.N):
        for j in range(board.N):
            if board.get(i, j) == board.empty:
                new_board[i][j] = 1

    return new_board