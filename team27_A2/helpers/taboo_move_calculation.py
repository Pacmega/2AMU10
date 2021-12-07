from typing import Dict, Tuple, List, Set

from competitive_sudoku.sudoku import GameState


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
        for number in range(1, game_state.board.N, 1):
            rows_containing_number = 0
            for j in range(i, i + rows_per_block, 1):
                if number not in allowed_in_rows[j]:
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

                    for row_index in range(i, i + rows_per_block, 1):
                        for col_index in range(j, j + columns_per_block, 1):
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
                for row in range(i, i + rows_per_block, 1):
                    if number in allowed_in_rows[row] and row in newly_occupied_rows:
                        rows_to_check.append(row)

                for block in blocks_to_check:
                    for row in rows_to_check:
                        for j in range(block[1], block[1] + columns_per_block, 1):
                            if (row, j) in legal_moves:
                                if number in legal_moves[(row, j)]:
                                    legal_moves[(row, j)].remove(number)

    return legal_moves
