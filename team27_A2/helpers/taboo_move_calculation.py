from typing import Dict, Tuple, List, Set

from competitive_sudoku.sudoku import GameState

from . import get_block_top_left_coordinates


def locked_candidates_rows(game_state: GameState,
                           legal_moves: Dict[Tuple[int, int], List[int]],
                           allowed_in_rows: List[Set[int]],
                           allowed_in_blocks: Dict[Tuple[int, int], List[int]]):
    rows_per_block = game_state.board.m
    columns_per_block = game_state.board.n
    if rows_per_block <= 2:
        return legal_moves

    for i in range(0, game_state.board.N, columns_per_block):
        incomplete_numbers = []
        for number in range(1, game_state.board.N):
            rows_containing_number = 0
            for ii in range(i, i + rows_per_block):
                if number not in allowed_in_rows[ii]:
                    rows_containing_number += 1

            if rows_per_block - rows_containing_number >= 2:
                incomplete_numbers.append(number)

        for number in incomplete_numbers:
            # check whether there is a block that only has one row where this number should go
            #   first, check if block already contains the number, if so, move to the next
            #   second, check which rows have empty squares
            #   third, check how many of these rows allow this number
            #   if only one row allows this number, then bingo

            newly_occupied_blocks = []
            newly_occupied_rows = []
            for j in range(0, game_state.board.N, rows_per_block):
                if number in allowed_in_blocks[(i, j)]:
                    rows_allowing_number = []

                    for row_index in range(i, i + rows_per_block):
                        for col_index in range(j, j + columns_per_block):
                            if (row_index, col_index) in legal_moves and number in legal_moves[(row_index, col_index)]:
                                rows_allowing_number.append(row_index)
                                break

                    if len(rows_allowing_number) == 1:
                        newly_occupied_blocks.append((i, j))
                        newly_occupied_rows.append(rows_allowing_number[0])

            if len(newly_occupied_rows) > 0:
                # Then the other block cannot put the number in that row
                blocks_to_check = []
                for j in range(0, game_state.board.N, rows_per_block):
                    if (i, j) not in newly_occupied_blocks and number in allowed_in_blocks[(i, j)]:
                        blocks_to_check.append((i, j))

                rows_to_check = []
                for row in range(i, i + rows_per_block):
                    if number in allowed_in_rows[row] and row in newly_occupied_rows:
                        rows_to_check.append(row)

                for block in blocks_to_check:
                    for row in rows_to_check:
                        for j in range(block[1], block[1] + columns_per_block):
                            if (row, j) in legal_moves and number in legal_moves[(row, j)]:
                                legal_moves[(row, j)].remove(number)

    return legal_moves


def locked_candidates_columns(game_state: GameState,
                              legal_moves: Dict[Tuple[int, int], List[int]],
                              allowed_in_columns: List[Set[int]],
                              allowed_in_blocks: Dict[Tuple[int, int], List[int]]):
    rows_per_block = game_state.board.m
    columns_per_block = game_state.board.n
    if columns_per_block <= 2:
        return legal_moves

    for j in range(0, game_state.board.N, rows_per_block):
        incomplete_numbers = []
        for number in range(1, game_state.board.N):
            columns_containing_number = 0
            for jj in range(j, j + columns_per_block):
                if number not in allowed_in_columns[jj]:
                    columns_containing_number += 1

            if columns_per_block - columns_containing_number >= 2:
                incomplete_numbers.append(number)

        for number in incomplete_numbers:
            newly_occupied_blocks = []
            newly_occupied_columns = []
            for i in range(0, game_state.board.N, columns_per_block):
                if (i, j) in allowed_in_blocks and number in allowed_in_blocks[(i, j)]:
                    columns_allowing_number = []

                    for col_index in range(j, j + columns_per_block):
                        for row_index in range(i, i + rows_per_block):
                            if (row_index, col_index) in legal_moves and number in legal_moves[(row_index, col_index)]:
                                columns_allowing_number.append(col_index)
                                break

                    if len(columns_allowing_number) == 1:
                        newly_occupied_blocks.append((i, j))
                        newly_occupied_columns.append(columns_allowing_number[0])

            if len(newly_occupied_columns) > 0:
                blocks_to_check = []
                for i in range(0, game_state.board.N, columns_per_block):
                    if (i, j) not in newly_occupied_blocks and (i, j) in allowed_in_blocks and \
                            number in allowed_in_blocks[(i, j)]:
                        blocks_to_check.append((i, j))

                columns_to_check = []
                for col in range(j , j + columns_per_block):
                    if number in allowed_in_columns[col] and col in newly_occupied_columns:
                        columns_to_check.append(col)

                for block in blocks_to_check:
                    for col in columns_to_check:
                        for i in range(block[0], block[0] + rows_per_block):
                            if (i, col) in legal_moves and number in legal_moves[(i, col)]:
                                legal_moves[(i, col)].remove(number)

        return legal_moves


def obvious_singles(game_state: GameState,
                  legal_moves: Dict[Tuple[int, int], List[int]]):
    # TODO: Needs manual checking to confirm correctness
    for possible_single_cell in legal_moves:
        if len(legal_moves[possible_single_cell]) == 1:
            # This cell contains exactly a single possible value,
            #   so clearly that value has to go here
            single_row = possible_single_cell[0]
            single_column = possible_single_cell[1]
            single_value = legal_moves[possible_single_cell][0]

            first_block_row, first_block_column = get_block_top_left_coordinates(
                single_row, single_column, game_state.board.m, game_state.board.n)

            for i in range(game_state.board.N):
                # This doesn't crash, since Python immediately continues
                #    if the first part of the if statement is False
                if i != single_row and (i, single_column) in legal_moves and \
                        single_value in legal_moves[(i, single_column)]:
                    legal_moves[(i, single_column)].remove(single_value)

                if i != single_column and (single_row, i) in legal_moves and \
                        single_value in legal_moves[(single_row, i)]:
                    legal_moves[(single_row, i)].remove(single_value)

                block_cell_row = first_block_row + (i // game_state.board.m)
                block_cell_column = first_block_column + (i % game_state.board.n)

                if not (block_cell_row == single_row and block_cell_column == single_column) and \
                        (block_cell_row, block_cell_column) in legal_moves and \
                        single_value in legal_moves[(block_cell_row, block_cell_column)]:
                    legal_moves[(block_cell_row, block_cell_column)].remove(single_value)

    return legal_moves


def hidden_singles(game_state: GameState, legal_moves: Dict[Tuple[int, int], List[int]]):
    # TODO: Needs manual checking to confirm correctness
    # Create (initially empty) lists and a small matrix to store for every row/column/block (unit)
    #   which values within that unit have already been determined to not possibly be singles
    #   (== are legal in > 1 cell within that unit)
    non_singles_row = [[] for i in range(game_state.board.N)]
    non_singles_column = [[] for i in range(game_state.board.N)]
    non_singles_block = [[[] for col_block in range(game_state.board.N // game_state.board.n)] \
                             for row_block in range(game_state.board.N // game_state.board.m)]

    for possible_single_cell in legal_moves:
        cell_row = possible_single_cell[0]
        cell_column = possible_single_cell[1]

        cell_block_row = cell_row // game_state.board.m
        cell_block_column = cell_column // game_state.board.n

        first_block_row, first_block_column = get_block_top_left_coordinates(
            cell_row, cell_column, game_state.board.m, game_state.board.n)

        for possible_value in legal_moves[possible_single_cell]:
            potential_single_in_row = True
            potential_single_in_column = True
            potential_single_in_block = True

            if possible_value in non_singles_row[cell_row]:
                potential_single_in_row = False

            if possible_value in non_singles_column[cell_column]:
                potential_single_in_column = False

            if possible_value in non_singles_block[cell_block_row][cell_block_column]:
                potential_single_in_block = False

            if not potential_single_in_row and not potential_single_in_column and \
                    not potential_single_in_block:
                # It is already clear that we don't need to look further
                continue

            for i in range(game_state.board.N):
                checking_block_cell_row = first_block_row + (i // game_state.board.n)
                checking_block_cell_column = first_block_column + (i % game_state.board.n)

                if not potential_single_in_row and not potential_single_in_column and \
                        not potential_single_in_block:
                    # In every possible way, this value is definitely not uniquely legal in this cell
                    break

                if potential_single_in_row and cell_column != i and \
                        (cell_row, i) in legal_moves and possible_value in legal_moves[(cell_row, i)]:
                    # Counterexample, this column has >= 2 places where this value is legal
                    potential_single_in_row = False
                    non_singles_row[cell_row].append(possible_value)

                if potential_single_in_column and cell_row != i and \
                        (i, cell_column) in legal_moves and possible_value in legal_moves[(i, cell_column)]:
                    # Counterexample, this row has >= 2 places where this value is legal
                    potential_single_in_column = False
                    non_singles_column[cell_column].append(possible_value)

                if potential_single_in_block and not (checking_block_cell_row == cell_row and \
                        checking_block_cell_column == cell_column) and \
                        (checking_block_cell_row, checking_block_cell_column) in legal_moves and \
                        possible_value in legal_moves[(checking_block_cell_row, checking_block_cell_column)]:
                    # Counterexample, this block has >= 2 places where this value is legal
                    potential_single_in_block = False
                    block_index_row = checking_block_cell_row // game_state.board.m
                    block_index_column = checking_block_cell_column // game_state.board.n
                    non_singles_block[block_index_row][block_index_column].append(possible_value)

            # After checking all cells in the corresponding rows/columns/block,
            #   if this value-cell combination is indeed unique to one of those three
            #   this cell must contain this particular value. Replace the list of potential
            #   values with a list carrying this one value. This works safely, despite us here
            #   modifying the list we are currently iterating over.
            if potential_single_in_row or potential_single_in_column or potential_single_in_block:
                legal_moves[possible_single_cell] = [possible_value]

    return legal_moves
