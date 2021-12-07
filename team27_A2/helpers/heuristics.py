from typing import Dict, Tuple, List


def remove_squares_with_many_options(moves_under_consideration: Dict[Tuple[int, int], List[int]],number_of_options: int):
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
