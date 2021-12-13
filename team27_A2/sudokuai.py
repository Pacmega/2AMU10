from typing import List
from collections import defaultdict
import random

from competitive_sudoku.sudoku import GameState, Move
import competitive_sudoku.sudokuai

from team27_A2.helpers import game_helpers, heuristics, taboo_move_calculation


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration. This particular
    implementation is the agent of group 27 for Foundations of AI which employs a minimax algorithm with the extension
    of alpha-beta pruning.
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
            """
            self.game_state = game_state
            self.children: List[SudokuAI.Node] = []

        def extend_node(self):
            """
            This function expands the node with the valuable moves as calculated by the agent.
            First, it gets the valuable moves from the agent.
            Then, it loops over all determined valuable moves, simulates these moves, creates a new node with the new
                game state and appends this new node to the list of children.
            """
            if len(self.children) > 0:
                raise Exception("extend tree should not be called on an already extended node!")

            valuable_moves = SudokuAI.get_valuable_moves(self.game_state)

            for move in valuable_moves:
                new_game_state = game_helpers.simulate_move(self.game_state, move)
                self.children.append(SudokuAI.Node(new_game_state))

    def compute_best_move(self, game_state: GameState) -> None:
        """
        Main agent function to call. This function iteratively explores the
        possible moves and future states of the game via a minimax algorithm
        including A-B pruning, and continues to search further for as long as
        it is allowed. This function does not terminate in normal execution.
        @param game_state:  The current GameState that the next move should be
                                computed for.
        @return:            Nothing. (function should not terminate in normal execution)
        """
        i = 1
        max_depth = 20

        # Initialize the root node, which is going to keep track of all the explored states.
        root = self.Node(game_state)

        # Suggest a random legal move at first to make sure we always have something
        root.extend_node()
        self.propose_move(random.choice(root.children).game_state.moves[-1])

        while i < max_depth:
            if game_helpers.board_filled_in(root.game_state):
                break

            # Which player we are can be deduced from the number of previous
            #   moves, and from that we can tell whether we want to maximize
            #   or minimize our evaluation function (score P1 - score P2)
            maximizing_player = not bool(len(root.game_state.moves) % 2)

            value, optimal_move = self.minimax(root, i, maximizing_player, -100000, 100000)
            print(value)
            if optimal_move is None:
                break
            else:
                self.propose_move(optimal_move)

            print("Completed depth: " + str(i))

            i += 1

    def minimax(self, node: Node, depth: int, maximizing_player: bool, alpha: int, beta: int) -> (int, Move):
        """
        The minimax algorithm used by this agent to find the best move possible,
        also using Alpha-Beta pruning in order to stops evaluating a move sooner
        when at least one possibility has been found that proves the move to be
        worse than a previously examined move.
        @param game_state:          The current GameState that the next move should be computed for.
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
                    # A more optimal (or the first functional) move was found, start maintaining
                    #   a list of moves with this value so that we can pick one of those to play

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
                    # A more optimal (or the first functional) move was found, start maintaining
                    #   a list of moves with this value so that we can pick one of those to play
                    best_move = child.game_state.moves[-1]
                    value = new_value

                beta = min(beta, value)

                if value <= alpha:
                    break
            return value, best_move

    @staticmethod
    def get_valuable_moves(game_state: GameState) -> List[Move]:
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
        # Use heuristics to discover legal moves that would be taboo
        ###
        # TODO: Discover the best order of heuristic applications
        # TODO: confirm that taboo moves functions as intended

        taboo_move_calculation.obvious_singles(game_state, legal_moves, taboo_moves)
        taboo_move_calculation.hidden_singles(game_state, legal_moves, taboo_moves)

        taboo_move_calculation.locked_candidates_rows(game_state, legal_moves, rows, blocks, taboo_moves)
        taboo_move_calculation.locked_candidates_columns(game_state, legal_moves, columns, blocks, taboo_moves)

        taboo_move_calculation.obvious_singles(game_state, legal_moves, taboo_moves)
        taboo_move_calculation.hidden_singles(game_state, legal_moves, taboo_moves)

        ###
        # Then, use heuristics to help choose the best possible moves
        ###

        legal_moves = heuristics.force_highest_points_moves(game_state, legal_moves, rows, columns, blocks)
        legal_moves = heuristics.remove_moves_that_allows_opponent_to_score(game_state, legal_moves, rows, columns,
                                                                            blocks)
        legal_moves = heuristics.one_move_per_square(legal_moves)

        # Write everything to a list
        moves_list = []
        for square in legal_moves.keys():
            moves: List[int] = legal_moves[square]
            for move in moves:
                moves_list.append(Move(square[0], square[1], move))

        random.shuffle(moves_list)
        return moves_list

    def evaluate(self, game_state: GameState):
        """
        Calculate the heuristic that is used by the minimax algorithm
        to see which moves and options are good for either player.
        Calculation used: Player 1's score - Player 2's score
        """

        # The player we are simulating for, either P1 or P2, can be deduced
        #   from the length of the move history (player 1 always goes first)
        simulating_for = not bool(len(game_state.moves) % 2)

        score = game_state.scores[0] - game_state.scores[1]

        return score
