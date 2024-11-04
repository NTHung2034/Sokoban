import heapq
from typing import List, Tuple, Set, Dict
import time
import psutil
from dataclasses import dataclass

# Maximum time (in seconds) allowed for solving a maze before timing out
time_out = 60

@dataclass(frozen=True)
class Position:
    x: int  
    y: int 
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

class State:
    def __init__(self, player: Position, stone_weights: Dict[Position, int], cost: int = 0):
        self.player = player
        self.stone_weights = stone_weights  # Dictionary mapping stone positions to their weights
        self.cost = cost  # Total cost to reach this state (moves + weight of pushed stones)
        
    def __lt__(self, other):
        return self.cost < other.cost
        
    def __eq__(self, other):
        return (self.player == other.player and self.stone_weights == other.stone_weights)
        
    def __hash__(self):
        return hash((self.player, frozenset(self.stone_weights.items())))

class MazeSolver:
    def __init__(self, maze: List[str], stone_weights: List[int]):
        # Clean up the maze input and ensure all rows have same width
        self.maze = [row.rstrip() for row in maze] 
        self.width = max(len(row) for row in self.maze)
        self.maze = [row.ljust(self.width) for row in self.maze]
        self.height = len(self.maze)
        
        self.switches = set()  # switches positions
        self.walls = set()  # wall positions
        self.nodes_generated = 0  
        self.start_pos = None  # start position of Ares
        
        # Initialize stone positions and weights
        stone_positions = {}
        stone_idx = 0
        
        # First pass: find switches and walls
        for i in range(self.height):
            for j in range(self.width):
                pos = Position(i, j)
                cell = self.maze[i][j]
                
                if cell == '#':
                    self.walls.add(pos)
                elif cell in ['.', '*', '+']:  # All switch positions
                    self.switches.add(pos)
                    
        # Second pass: find stones and player
        for i in range(self.height):
            for j in range(self.width):
                pos = Position(i, j)
                cell = self.maze[i][j]
                
                if cell in ['$', '*']:  # Stone or stone on switch
                    if stone_idx < len(stone_weights):
                        stone_positions[pos] = stone_weights[stone_idx]
                        stone_idx += 1
                elif cell in ['@', '+']:  # Player or player on switch
                    self.start_pos = pos
                    
        # Validate maze setup
        if self.start_pos is None:
            raise ValueError("No starting position '@' found in maze")
            
        if stone_idx != len(stone_weights):
            raise ValueError(f"Mismatch between number of stones in maze ({stone_idx}) and weights provided ({len(stone_weights)})")
            
        self.initial_stone_weights = stone_positions

        if len(self.switches) != len(stone_positions):
            raise ValueError(f"Mismatch between number of switches ({len(self.switches)}) and stones ({len(stone_positions)})")

    def is_valid_pos(self, pos: Position) -> bool:
        """Check if a position is within maze bounds and not a wall"""
        return (0 <= pos.x < self.height and 0 <= pos.y < self.width and pos not in self.walls)

    def get_initial_state(self) -> State:
        """Create the initial state of the maze"""
        return State(self.start_pos, self.initial_stone_weights)

    def is_goal_state(self, state: State) -> bool:
        """
        Check if current state is a goal state
        Goal: All stones are on switches (and number of stones equals number of switches)
        """
        stone_positions = set(state.stone_weights.keys())
        return stone_positions.issubset(self.switches) and len(stone_positions) == len(self.switches)

    def get_neighbors(self, state: State) -> List[Tuple[State, str]]:
        """
        Generate all possible next states from current state
        Returns list of (new_state, move) pairs where move is the action taken:
        - lowercase (u,d,l,r) for simple moves
        - uppercase (U,D,L,R) for pushing stones
        """
        neighbors = []
        moves = [
            (Position(-1, 0), 'u', 'U'),  # up
            (Position(1, 0), 'd', 'D'),   # down
            (Position(0, -1), 'l', 'L'),  # left
            (Position(0, 1), 'r', 'R')    # right
        ]

        for delta, move_char, push_char in moves:
            new_pos = state.player + delta 
            
            if not self.is_valid_pos(new_pos):
                continue
                
            stones = set(state.stone_weights.keys())
            
            # Case 1: Moving to empty space
            if new_pos not in stones:
                neighbors.append((State(new_pos, state.stone_weights, state.cost + 1), move_char))
            # Case 2: Pushing a stone
            else:
                push_pos = new_pos + delta  # Position where stone will end up
                if (self.is_valid_pos(push_pos) and push_pos not in stones):
                    # Create new stone positions dictionary with pushed stone
                    new_stone_weights = dict(state.stone_weights)
                    stone_weight = new_stone_weights.pop(new_pos)
                    new_stone_weights[push_pos] = stone_weight
                    
                    # Cost increases by 1 (for move) plus weight of pushed stone
                    push_cost = state.cost + 1 + stone_weight
                    neighbors.append((
                        State(new_pos, new_stone_weights, push_cost),
                        push_char
                    ))

        return neighbors

    def solve_ucs(self) -> Tuple[List[str], Dict]:
        """
        Solve maze using Uniform Cost Search (UCS) algorithm
        Returns:
        - Solution path as list of moves
        - Statistics dictionary with steps, weight, nodes explored, time, and memory usage
        """
        # Initialize process for memory monitoring
        process = psutil.Process()
        start_time = time.time()
        
        initial_state = self.get_initial_state()
        pq = [(0, [], initial_state)]  # Priority queue: (cost, path, state)
        visited = set()  # Keep track of visited states to avoid cycles
        
        while pq:
            cost, path, current_state = heapq.heappop(pq)

            # Check for timeout
            if time.time() - start_time > time_out:
                print("Timeout reached. Exiting UCS.")
                memory_used = process.memory_info().rss / (1024 ** 2)  # Convert to MB
                stats = {
                    'steps': len(path),
                    'weight': cost - len(path),  # Total weight = cost - number of moves
                    'nodes': self.nodes_generated,
                    'time': (time.time() - start_time) * 1000,  # Convert to milliseconds
                    'memory': memory_used
                }
                return None, stats  
            
            # Skip if state already visited
            if current_state in visited:
                continue
                
            visited.add(current_state)
            
            # Check if goal reached
            if self.is_goal_state(current_state):
                memory_used = process.memory_info().rss / (1024 ** 2)
                total_push_weight = cost - len(path)
                stats = {
                    'steps': len(path),
                    'weight': total_push_weight,
                    'nodes': self.nodes_generated,
                    'time': (time.time() - start_time) * 1000,
                    'memory': memory_used
                }
                return path, stats
            
            # Explore neighbors
            for next_state, move in self.get_neighbors(current_state):
                if next_state not in visited:
                    self.nodes_generated += 1
                    heapq.heappush(pq, (
                        next_state.cost,
                        path + [move],
                        next_state
                    ))
        
        # No solution found
        memory_used = process.memory_info().rss / (1024 ** 2)
        stats = {
            'steps': len(path),
            'weight': cost - len(path),
            'nodes': self.nodes_generated,
            'time': (time.time() - start_time) * 1000,
            'memory': memory_used
        }
        return None, stats

def read_input(filepath: str) -> Tuple[List[int], List[str]]:
    """Read stone weights and maze layout from input file"""
    with open(filepath, 'r') as f:
        stone_weights = list(map(int, f.readline().strip().split()))
        maze = [line.rstrip('\n') for line in f.readlines()]
    return stone_weights, maze

def write_output(filepath: str, solution: List[str], stats: Dict):
    """Write solution path and statistics to output file"""
    with open(filepath, 'a') as f:
        f.write('UCS\n')
        f.write(f"Steps: {stats['steps']}, Weight: {stats['weight']}, " +
                f"Nodes: {stats['nodes']}, Time (ms): {stats['time']:.2f}, " +
                f"Memory (MB): {stats['memory']:.2f}\n")
        f.write(f"{''.join(solution) if solution else 'No solution'}\n")

def solve_maze(input_path: str, output_path: str):
    """Main function to solve a single maze puzzle"""
    stone_weights, maze = read_input(input_path)
    solver = MazeSolver(maze, stone_weights)
    solution, stats = solver.solve_ucs()
    write_output(output_path, solution, stats)

def main():
    """Process all test cases from input-1.txt to input-10.txt"""
    for i in range(1, 11):
        input_file = f'Test_cases\\input-{i}.txt'
        output_file = f'Outputs\\output-{i}.txt'
        solve_maze(input_file, output_file)

if __name__ == "__main__":
    main()