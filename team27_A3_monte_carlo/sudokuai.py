from typing import List, Tuple
from collections import defaultdict
from copy import deepcopy
import random
import math

from competitive_sudoku.sudoku import GameState, Move, TabooMove
import competitive_sudoku.sudokuai

from team27_A3_monte_carlo.helpers import game_helpers, heuristics, taboo_move_calculation

class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration. This particular implementation
    is the agent of group 27 for Foundations of AI which employs a Monte Carlo Tree Search algorithm,
    and applying a number of heuristics to play not only legal but also good moves.
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

        def __init__(self, game_state: GameState, frequent_visit_c: float = 2):
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

            # Monte Carlo specific variables
            self.score_obtained = 0
            self.number_visits = 0
            self.frequent_visit_C = frequent_visit_c
            self.uct = float('inf')
            self.uct_needs_update = True

        def calculate_uct(self, parent_number_visits) -> float:
            """
            TODO: docstring
            """
            if self.number_visits == 0:
                # Avoid a division by 0, plus since this node was not visited before
                #   we should do that anyway
                self.uct = float('inf')
                self.uct_needs_update = False
                return

            # Variable names inspired by L9 lecture, slide 8
            # Note that by default, math.log() uses math.e as base making log as ln
            average_leaf_score = self.score_obtained / self.number_visits
            frequent_visit_penalty = self.frequent_visit_C \
                                     * math.sqrt(math.log(parent_number_visits) / self.number_visits)

            self.uct = average_leaf_score + frequent_visit_penalty
            self.uct_needs_update = False

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
            # print(len(taboo_moves))

            if 0 < len(taboo_moves) < 20 and self._want_to_play_taboo(can_score):
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
            # TODO: This part is temporarily disabled because Monte Carlo doesn't seem to always want to score points.
            if can_score:
                # If we can score, we definitely don't want to play a taboo move and let the opponent score
                return False
            elif game_helpers.even_number_of_squares_left(self.game_state) and \
                    game_helpers.board_half_filled_in(self.game_state):
                # We can't score, we are not playing from a position we want to be in, so use this
                #   chance to swap turns
                return True
            else:
                # Can't score right now, but our position is acceptable. Just play normally.
                return False

        def simulate_playout(self) -> (bool, int):
            """
            TODO: docstring
            """
            current_state = deepcopy(self.game_state)

            while True:
                # Keep playing moves until the board is completely full, or a state is reached
                #   where no valid moves exist but the board isn't full (meaning somewhere a taboo was missed)

                if game_helpers.board_filled_in(current_state):
                    # Simulated playout completed, check which player won (evaluation = 0 is a draw)
                    evaluation = current_state.scores[0] - current_state.scores[1]

                    if evaluation > 0:
                        # Player 1 won
                        evaluation = 1
                    elif evaluation < 0:
                        # Player 2 won
                        evaluation = 2

                    # Return that completion was successful, and attach the winning player
                    return True, evaluation

                # In this simulation we only care about moves_list, since we are playing random legal moves.
                moves_list, _, _ = SudokuAI.get_valuable_moves(current_state)

                if not moves_list and not game_helpers.board_filled_in(current_state):
                    # Return that completion was NOT successful, and attach a 0 score (the score should not be used).
                    return False, 0

                # Moves are shuffled within the list before it is returned, so picking the
                #   first one == random legal move. Play a random move, then keep going.
                current_state = game_helpers.simulate_move(current_state, moves_list[0], False)

    def treewalk_uct_checkup(self, node: Node):
        """
        TODO: docstring
        This does not check or update the root's UCT, but the root has no UCT.
        """
        for child in node.children:
            if child.uct_needs_update:
                child.calculate_uct(node.number_visits)
            self.treewalk_uct_checkup(child)

    def compute_best_move(self, game_state: GameState) -> None:
        """
        TODO: text incorrect
        Main agent function to call. This function iteratively explores the possible moves and
        future states of the game via a minimax algorithm including A-B pruning,
        and continues to search further for as long as it is allowed.
        This function does not ever return, unless a taboo move is played.
        @param game_state:  The current GameState that the next move should be computed for.
        @return:            Nothing.
        """
        # Initialize the root node, which is going to keep track of everything.
        root = self.Node(game_state)

        # Since extend node adds randomly ordered legal moves, picking the first == picking randomly.
        root.extend_node()
        self.propose_move(root.children[0].game_state.moves[-1])

        if root.playing_taboo:
            # No real need to bother with Monte Carlo if we're playing taboo moves
            # (if we are, the root's children are all taboo moves and a random one was suggested)
            return

        # TODO: Add a comment explaining what this is
        self.treewalk_uct_checkup(root)

        # Which player we are can be deduced from the number of previous
        #   moves, and from that we can tell whether we want to maximize
        #   or minimize our evaluation function (score P1 - score P2).
        # As can be seen from the evaluation function too, P1 is maximizing.
        root_is_player_1 = not bool(len(root.game_state.moves) % 2)

        while True:
            # Complete an iteration of Monte Carlo Tree Search.
            # self.pre_order_treewalk(root)
            # TODO: can_score is currently not being used, and that is obvious in move 1
            # print("Monte Carlo goes brr")
            self.monte_carlo(root, root_is_player_1)
            self.treewalk_uct_checkup(root)
            # self.pre_order_treewalk(root)

            # Pick best move to suggest
            optimal_move = None
            highest_uct = float('-inf')

            for child in root.children:
                if child.uct_needs_update:
                    raise Exception('UCT was not updated on time')
                if child.uct != float('inf') and child.uct > highest_uct:
                    # New record UCT and this node was visited at least once,
                    #   track and track current record holder child.
                    highest_uct = child.uct
                    optimal_move = child.game_state.moves[-1]

            # print(optimal_move)
            if optimal_move:
                self.propose_move(optimal_move)

    def monte_carlo(self, node: Node, root_is_player_1: bool) -> (bool, int):
        """
        TODO: docstring
        """
        # TODO: How well does this work? Does it even work as intended?
        # Leaf selection
        highest_uct = float('-inf')
        optimal_child = None

        for child in node.children:
            if child.uct_needs_update:
                raise Exception('UCT was not updated on time')
            if child.uct == float('inf'):
                # At most we find more of these, which would not break this score. Use this child.
                # print('Inf child UCT found: exploring.')
                optimal_child = child
                break

            if child.uct > highest_uct:
                # print(f'New record UCT: {child_uct}')
                # New record UCT, track it and the current record holder child.
                highest_uct = child.uct
                optimal_child = child

        # If there is an optimal child, we need to dive further down to find a potential leaf.
        if optimal_child:
            successful_simulation, winning_player = self.monte_carlo(optimal_child, root_is_player_1)
        else:
            if game_helpers.board_filled_in(node.game_state):
                # This node is a terminal state. Proceed to backpropagation.
                successful_simulation = True
                winning_player = node.game_state.scores[0] - node.game_state.scores[1]
            else:
                # If this is our first visit to this node, we simulate from here. If not, knowing that
                #   we are in the visiting step and this is not a terminal state, it can have children
                #   but doesn't yet. Enter leaf expansion step, and afterwards simulate from arbitrary leaf.
                if node.number_visits == 0:
                    # Simulate random playout from this node
                    successful_simulation, winning_player = node.simulate_playout()
                    # print(successful_simulation)
                else:
                    # Not the first time visiting this node, it is not a terminal state, but it does not have
                    #   children. It clearly can have children, so it is time to create those and simulate
                    #   from an arbitrary one of those. Calling monte_carlo again achieves that, since this
                    #   "arbitrary leaf" would be visited for the first time.
                    node.extend_node()
                    for child in node.children:
                        child.calculate_uct(node.number_visits)
                    # Since extend node adds randomly ordered legal moves, picking the first == picking random move.
                    random_leaf = node.children[0]
                    successful_simulation, winning_player = self.monte_carlo(random_leaf, root_is_player_1)

        # Backpropagation should only be done if the game was successfully simulated to a final state.
        if successful_simulation:
            # Backpropagation step: we now know who won the game in the eventual leaf. Update the score and
            #   visit counts for this current node (which might be the leaf that ran the simulation, or its
            #   parent, or further up the tree) and throw the winning_player further up the tree via recursion
            #   so that every node on the way up can do the same.
            node.number_visits += 1

            # The score_obtained on root's own turn (even depths) should always be <= 0,
            #   and that on the opponent's nodes (odd depths) should always be >= 0.
            node_is_player_1 = not bool(len(node.game_state.moves) % 2)
            node_is_winner = (winning_player == 1 and node_is_player_1) or \
                             (winning_player == 2 and not node_is_player_1)

            # Logic here is based on slides 15 & 16 (on-slide numbers) of the lecture slides L9_v2
            if (winning_player == 1 and root_is_player_1) or (winning_player == 2 and not root_is_player_1):
                if node_is_winner:
                    node.score_obtained -= 1
                else:
                    node.score_obtained += 1

            node.uct_needs_update = True

        return successful_simulation, winning_player


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

        return moves_list, taboo_list, can_score