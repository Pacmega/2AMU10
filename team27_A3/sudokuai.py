from typing import List, Tuple
from collections import defaultdict
import random
import numpy as np

from competitive_sudoku.sudoku import GameState, Move, TabooMove
import competitive_sudoku.sudokuai

from team27_A3.helpers import game_helpers, heuristics, taboo_move_calculation


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration. This particular implementation
    is the agent of group 27 for Foundations of AI which employs a minimax algorithm with the extension
    of alpha-beta pruning, and applying a number of heuristics to play not only legal but also good moves.
    """

    def __init__(self):
        """
        Create a new SudokuAI agent, using nothing particular that was not
        already present in the original implementation this agent inherits
        its basic capabilities from.
        """
        super().__init__()

    class Node:
        """
        The Node inner class stores a game state and its respective subtree. For the minimax, a root node is created
        which is used throughout the iterative deepening process to minimize duplicate calculations.
        """

        def __init__(self, game_state: GameState):
            """
            Creates a new Node, stores the given game state, and initializes an empty list of children.
            @param game_state: The GameState that this node should build around.
            @return:           An instantiated instance of the Node class.
            """
            self.game_state = game_state
            self.children: List[SudokuAI.Node] = []
            # This playing_taboo variable is relevant because we do not make use of the future when
            #   we're playing a taboo move, so exploring said future is a waste of resources.
            self.playing_taboo = False

        def extend_node(self):
            """
            This function expands the node with the valuable moves as calculated by the agent.
            First, it gets the valuable moves from the agent.
            Then, it loops over all determined valuable moves, simulates these moves, creates a new node with the new
                game state and appends this new node to the list of children.
            @return: Nothing.
            """
            if len(self.children) > 0:
                raise Exception("extend tree should not be called on an already extended node!")

            valuable_moves, taboo_moves, can_score = SudokuAI.get_valuable_moves(self.game_state)

            if 0 < len(taboo_moves) < 20 and len(taboo_moves) % 2 == 1 and self._want_to_play_taboo(can_score):
                # We want to play a taboo move here, and there are legal taboo moves available
                self.playing_taboo = True

                taboo_move_to_play = taboo_moves[0]
                new_game_state = game_helpers.simulate_move(self.game_state, taboo_move_to_play, True)
                self.children.append(SudokuAI.Node(new_game_state))
            else:
                # Create all valuable moves as new Node children of this Node, for minimax to explore
                for move in valuable_moves:
                    new_game_state = game_helpers.simulate_move(self.game_state, move, False)
                    self.children.append(SudokuAI.Node(new_game_state))

        def _want_to_play_taboo(self, can_score: bool) -> bool:
            """
            Creates a new Node, stores the given game state, and initializes an empty list of children.
            @param can_score: Boolean describing whether there are current valuable moves that could
                                  grant this player points.
            @return:          A boolean describing whether we want to play a taboo move in this state or not.
            """
            if can_score:
                # If we can score, we definitely don't want to play a taboo move and let the opponent score
                return False
            elif game_helpers.even_number_of_squares_left(self.game_state) and \
                    game_helpers.board_half_filled_in(self.game_state):
                # We can't score, we are not player from a position we want to be in, so use this
                #   chance to swap turns
                return True
            else:
                # Can't score right now, but our position is acceptable. Just play normally.
                return False

    def compute_best_move(self, game_state: GameState) -> None:
        """
        Main agent function to call. This function iteratively explores the possible moves and
        future states of the game via a minimax algorithm including A-B pruning,
        and continues to search further for as long as it is allowed.
        This function does not ever return, unless a taboo move is played.
        @param game_state:  The current GameState that the next move should be computed for.
        @return:            Nothing.
        """
        i = 1
        max_depth = 20

        # Initialize the root node, which is going to keep track of all the explored states.
        root = self.Node(game_state)

        # Suggest a random legal move at first to make sure we always have something
        root.extend_node()
        self.propose_move(random.choice(root.children).game_state.moves[-1])

        if root.playing_taboo:
            # No real need to bother with the minimax part if we're playing taboo moves
            return

        while i < max_depth:
            if game_helpers.board_filled_in(root.game_state):
                break

            # Which player we are can be deduced from the number of previous
            #   moves, and from that we can tell whether we want to maximize
            #   or minimize our evaluation function (score P1 - score P2)
            maximizing_player = not bool(len(root.game_state.moves) % 2)

            value, optimal_move = self.minimax(root, i, maximizing_player, -100000, 100000)
            if optimal_move is None:
                break
            else:
                self.propose_move(optimal_move)

            # print("Completed depth ", i)

            # And now that this depth is done, on to the next!
            i += 1

    def minimax(self, node: Node, depth: int, maximizing_player: bool, alpha: int, beta: int) -> (int, Move):
        """
        The minimax algorithm used by this agent to find the best move possible,
        also using Alpha-Beta pruning in order to stops evaluating a move sooner
        when at least one possibility has been found that proves the move to be
        worse than a previously examined move.
        @param node:                The Node in our tree structure that this minimax execution should
                                        find the next move for.
        @param depth:               The maximum amount of levels that the game tree should be explored up to.
        @param maximizing_player:   Boolean specifying whether the current player being evaluated is
                                        the one that wants to maximize the evaluation heuristic (Player 1).
        @param alpha:               The minimum score that the maximizing player is assured of
        @param beta:                The maximum score that the minimizing player is assured of
        @return:                    A tuple specifying the optimal value of the move (-s) for this player in the tree
                                        up to the depth given, and a list of length 1 or more containing said move (-s).
                                        (-100000, None) is returned if there is no move to play.
        """
        if depth == 0 or game_helpers.board_filled_in(node.game_state):
            return self.evaluate(node.game_state), None

        # Check if the next layer of the tree is already present
        #   If not, expand the tree
        if len(node.children) == 0:
            node.extend_node()

        if maximizing_player:
            value = -100000
            best_move = None

            for child in node.children:
                # For each of the children, run minimax again
                new_value, _ = self.minimax(child, depth - 1, False, alpha, beta)

                if new_value > value:
                    # A more optimal (or the first functional) move was determined,
                    #   so store its value and get the move from this child
                    best_move = child.game_state.moves[-1]
                    value = new_value

                alpha = max(alpha, value)

                if value >= beta:
                    break

            return value, best_move

        else:
            value = 1000000
            best_move = None

            for child in node.children:
                # For each of the children, run minimax again
                new_value, _ = self.minimax(child, depth - 1, True, alpha, beta)

                if new_value < value:
                    # A more optimal (or the first functional) move was determined,
                    #   so store its value and get the move from this child
                    best_move = child.game_state.moves[-1]
                    value = new_value

                beta = min(beta, value)

                if value <= alpha:
                    break
            return value, best_move

    @staticmethod
    def get_valuable_moves(game_state: GameState) -> Tuple[List[Move], List[Move], bool]:
        """
        This function computes all valuable moves, according to a set of heuristics, which are then to be explored by
        the minimax algorithm.
        First, it computes all legal moves (so already excluding taboo moves).
        Then, it reduces this set of legal moves through several heuristics.
        Lastly, it writes everything to a list of moves, which it then returns.
        @param game_state:  The game state for which the valuable moves have to be computed.
        @return:            A list of valuable moves.
        """

        # Get all legal moves, and allowed moves in each row, column and block.
        # Check the compute_all_legal_moves function for type specifications.
        (legal_moves, rows, columns, blocks) = game_helpers.compute_all_legal_moves(game_state)

        # Create a dictionary to carry the found taboo moves. Note that this defaultdict
        #   always returns a list of taboo moves for a cell, which is an empty list
        #   if there are no known values.
        taboo_moves = defaultdict(lambda: [])

        ###
        # Use heuristics to discover legal moves that would be taboo. This order of heuristics was found
        # through empirical testing to find the most taboo moves that should not be explored.
        ###

        taboo_move_calculation.obvious_singles(game_state, legal_moves, taboo_moves)
        taboo_move_calculation.hidden_singles(game_state, legal_moves, taboo_moves)

        taboo_move_calculation.locked_candidates_rows(game_state, legal_moves, rows, blocks, taboo_moves)
        taboo_move_calculation.locked_candidates_columns(game_state, legal_moves, columns, blocks, taboo_moves)

        taboo_move_calculation.obvious_singles(game_state, legal_moves, taboo_moves)
        taboo_move_calculation.hidden_singles(game_state, legal_moves, taboo_moves)

        # The heuristics might have removed so many values from some moves that there is not actually
        #   a move left to play for that cell. If this is the case, remove the entire cell key from the
        #   legal_moves dictionary.
        empty = []
        for key, value in legal_moves.items():
            if len(value) == 0:
                empty.append(key)

        for key in empty:
            legal_moves.pop(key)

        ###
        # Then use heuristics to help choose the best possible moves
        ###

        legal_moves = heuristics.force_highest_points_moves(game_state, legal_moves, rows, columns, blocks)
        legal_moves, can_score = heuristics.remove_moves_that_allows_opponent_to_score(game_state, legal_moves,
                                                                                       rows, columns, blocks)
        heuristics.one_move_per_square(legal_moves)

        # Write everything to two lists
        moves_list = []
        taboo_list = []

        for square in legal_moves:
            moves: List[int] = legal_moves[square]
            for move in moves:
                moves_list.append(Move(square[0], square[1], move))

        for square in taboo_moves:
            moves: List[int] = taboo_moves[square]
            for move in moves:
                taboo_list.append(TabooMove(square[0], square[1], move))

        random.shuffle(moves_list)
        random.shuffle(taboo_list)

        # If we can score, then it is beneficial for the pruning to first explore these moves.
        # So sort the array on whether the move scores points.
        sorted_moves_list = []
        if can_score:
            for move in moves_list:
                if len(rows[move.i]) == 1 or len(columns[move.j]) or \
                        len(blocks[game_helpers.get_block_top_left_coordinates(move.i, move.j, game_state.board.m,
                                                                               game_state.board.n)]):
                    sorted_moves_list.insert(0, move)
                else:
                    sorted_moves_list.append(move)

        return sorted_moves_list if can_score else moves_list, taboo_list, can_score

    @staticmethod
    def evaluate(game_state: GameState) -> int:
        """
        Calculate the heuristic that is used by the minimax algorithm
        to see which moves and options are good for either player.
        @param game_state: The specific GameState to calculate the value of.
        @return:           An integer describing the value of this state.
        """

        # First, as basis, take the score of the game.
        score = game_state.scores[0] - game_state.scores[1]

        # Get array of squares that are empty.
        number_positions = game_helpers.empty_spaces_as_numpy_array(game_state.board)

        # If no squares are empty, then just return the score. Game is over.
        if np.sum(number_positions) == 0:
            return score

        # Store who is next to play a move (either 0 or 1)
        next_to_play = len(game_state.moves) % 2

        # Initialize potential points variable to store results of additional calculations.
        potential_points = 0

        # Get the number of empty squares for each column.
        col_ones = np.ones((1, game_state.board.N), dtype=int)
        cols = np.resize(np.matmul(col_ones, number_positions), (game_state.board.N))

        # Create dictionary with (spots_free: number_of_columns)
        unique, counts = np.unique(cols, return_counts=True)
        col_occurrences = dict(zip(unique, counts))

        # Get the number of empty squares for each row
        row_ones = np.ones((game_state.board.N, 1), dtype=int)
        rows = np.resize(np.matmul(number_positions, row_ones), (game_state.board.N))

        # Create dictionary with (spots_free: number_of_rows)
        unique, counts = np.unique(rows, return_counts=True)
        row_occurrences = dict(zip(unique, counts))

        # Do the same for the blocks
        blocks = np.resize(
            np.resize(number_positions,
                      (game_state.board.n, game_state.board.m, game_state.board.m, game_state.board.n)).sum(
                axis=(1, 3)),
            (game_state.board.N))
        unique, counts = np.unique(blocks, return_counts=True)
        block_occurrences = dict(zip(unique, counts))

        # Now for the scoring.
        # If you can score in a block, column or row (meaning only 1 empty square left),
        #   then 0.2 is added to the potential points.
        # If there are 2 spots left, then 0.1 is removed from the potential points.

        if 1 in col_occurrences:
            potential_points += col_occurrences[1] * 0.2

        if 2 in col_occurrences:
            potential_points -= col_occurrences[2] * 0.1

        if 1 in row_occurrences:
            potential_points += row_occurrences[1] * 0.2

        if 2 in row_occurrences:
            potential_points -= row_occurrences[2] * 0.1

        if 1 in block_occurrences:
            potential_points += block_occurrences[1] * 0.2

        if 2 in block_occurrences:
            potential_points -= block_occurrences[2] * 0.1

        # Depending on who is next to play, points are either added or subtracted.
        if next_to_play == 0:
            score += potential_points
        else:
            score -= potential_points

        return score
