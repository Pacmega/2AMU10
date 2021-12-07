from copy import deepcopy
from typing import List, Set, Dict, Tuple

from competitive_sudoku.sudoku import GameState, Move

"""
This file contains functions that extend the functionality of the GameState class, such as calculating 
acceptable moves, checking whether the board still contains an empty square, or simulating a move on a GameState object.
"""


def board_filled_in(game_state: GameState) -> bool:
    """
    Helper function to check if there are any empty cells on the board.
    """
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if game_state.board.get(i, j) == game_state.board.empty:
                return False
    return True

def compute_all_legal_moves(game_state: GameState) \
        -> (Dict[Tuple[int, int], List[int]], List[Set[int]], List[Set[int]], Dict[Tuple[int, int], List[int]]):
    """
    Computes all the possible moves in the game state,
    minus the taboo moves specified by the GameState.
    @param game_state:  The GameState to compute all legal moves for.
    @return:            A tuple with 4 values:
                            (1) A dictionary with coordinates as keys, and lists of legal values for the respective
                                square as values.
                            (2) A list (size N) of sets, representing the allowed numbers in each row/
                            (3) A list (size N) of sets, representing the allowed numbers in each column
                            (4) A dictionary of coordinates as keys (top left square of a block),
                                with a set of the allowed numbers in the respective block as the value.
    """

    # First, get all allowed numbers for each of the rows and columns
    rows = []
    columns = []
    for i in range(game_state.board.N):
        rows.append(allowed_numbers_in_row(game_state, i))
        columns.append(allowed_numbers_in_column(game_state, i))

    # Next, get all allowed numbers for each of the blocks
    all_block_indices = [(i, j)
                         for i in range(0, game_state.board.N, game_state.board.m)
                         for j in range(0, game_state.board.N, game_state.board.n)]

    blocks = {}
    for block_index in all_block_indices:
        blocks[block_index] = allowed_numbers_in_block(game_state, block_index[0], block_index[1])

    # Consequently, loop over each of the empty squares and take the
    # intersection of allowed moves for the row, column and block for that square
    allowed_moves = {}
    for i in range(game_state.board.N):
        for j in range(game_state.board.N):
            if game_state.board.get(i, j) == game_state.board.empty:
                allowed_moves[(i, j)] = list(
                    rows[i].intersection(columns[j])
                        .intersection(blocks[get_block_top_left_coordinates(i, j,
                                                                            game_state.board.m, game_state.board.n)])
                )

    all_empty_squares = allowed_moves.keys()

    # Lastly, remove all taboo moves
    for taboo_move in game_state.taboo_moves:
        if (taboo_move.i, taboo_move.j) in list(all_empty_squares):
            square_moves = allowed_moves[(taboo_move.i, taboo_move.j)]
            if taboo_move.value in square_moves:
                allowed_moves.get((taboo_move.i, taboo_move.j)).remove(taboo_move.value)

    return allowed_moves, rows, columns, blocks


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


def simulate_move(game_state: GameState, move: Move) -> GameState:
    """
    Simulates the execution of the given Move on the given GameState. This function
    does not check whether a move might be taboo, and instead just executes it.
    The function internally deduces from the length of game_state.moves
    for which player the given move should be played.
    @param game_state:  The GameState to execute/simulate the given move on.
    @param move:        The move to execute/simulate on the given GameState.
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
    return row_index - (row_index % m), column_index - (column_index % n)
