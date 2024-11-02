# Tấn Hưng
import heapq
from typing import List, Tuple, Set, Dict
import time
import Modules.File as File
import psutil
import os
from dataclasses import dataclass
time_out = 20

@dataclass(frozen=True)
class Position:
    x: int
    y: int
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

class State:
    def __init__(self, player: Position, stone_weights: Dict[Position, int], cost: int = 0):
        self.player = player
        self.stone_weights = stone_weights
        self.cost = cost
        
    def __lt__(self, other):
        return self.cost < other.cost
        
    def __eq__(self, other):
        return (self.player == other.player and self.stone_weights == other.stone_weights)
        
    def __hash__(self):
        return hash((self.player, frozenset(self.stone_weights.items())))

class MazeSolver:
    def __init__(self, maze: List[str], stone_weights: List[int]):
        # Clean up the maze input
        self.maze = [row.rstrip() for row in maze] 
        self.width = max(len(row) for row in self.maze)
        self.maze = [row.ljust(self.width) for row in self.maze]
        self.height = len(self.maze)
        
        self.switches = set()
        self.walls = set()
        self.nodes_generated = 0
        self.start_pos = None
        
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
                elif cell in ['.', '*', '+']:
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
                    
        if self.start_pos is None:
            raise ValueError("No starting position '@' found in maze") # can't find Ares in the maze
            
        if stone_idx != len(stone_weights): # check if we have enough stones 
            raise ValueError(f"Mismatch between number of stones in maze ({stone_idx}) and weights provided ({len(stone_weights)})")
            
        self.initial_stone_weights = stone_positions

        # Verify we have same number of switches as stones
        if len(self.switches) != len(stone_positions):
            raise ValueError(f"Mismatch between number of switches ({len(self.switches)}) and stones ({len(stone_positions)})")

    def print_state(self, state: State):
        """Debug function to visualize current state"""
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Add walls
        for wall in self.walls:
            grid[wall.x][wall.y] = '#'
            
        # Add switches
        for switch in self.switches:
            grid[switch.x][switch.y] = '.'
            
        # Add stones
        for stone_pos in state.stone_weights.keys():
            if stone_pos in self.switches:
                grid[stone_pos.x][stone_pos.y] = '*'
            else:
                grid[stone_pos.x][stone_pos.y] = '$'
                
        # Add player
        if state.player in self.switches:
            grid[state.player.x][state.player.y] = '+'
        else:
            grid[state.player.x][state.player.y] = '@'
            
        return '\n'.join(''.join(row) for row in grid)

    def is_valid_pos(self, pos: Position) -> bool:
        return (0 <= pos.x < self.height and 0 <= pos.y < self.width and pos not in self.walls)

    def get_initial_state(self) -> State:
        return State(self.start_pos, self.initial_stone_weights)

    def is_goal_state(self, state: State) -> bool:
        # Check if all stones are on switches (more precise check)
        stone_positions = set(state.stone_weights.keys())
        return stone_positions.issubset(self.switches) and len(stone_positions) == len(self.switches)

    def get_neighbors(self, state: State) -> List[Tuple[State, str]]:
        neighbors = []
        moves = [
            (Position(-1, 0), 'u', 'U'),  # up
            (Position(1, 0), 'd', 'D'),   # down
            (Position(0, -1), 'l', 'L'),  # left
            (Position(0, 1), 'r', 'R')    # right
        ]

        for delta, move_char, push_char in moves:
            new_pos = state.player + delta 
            
            # Skip if new position is invalid
            if not self.is_valid_pos(new_pos):
                continue
                
            stones = set(state.stone_weights.keys())
            
            # Simple move (no stone)
            if new_pos not in stones:
                neighbors.append((State(new_pos, state.stone_weights, state.cost + 1), move_char))

            # Push move (stone present)
            else:
                push_pos = new_pos + delta # new pos of Ares = last pos of stone, push_pos = new pos of stone
                if (self.is_valid_pos(push_pos) and push_pos not in stones):
                    new_stone_weights = dict(state.stone_weights)
                    stone_weight = new_stone_weights.pop(new_pos)
                    new_stone_weights[push_pos] = stone_weight
                    
                    push_cost = state.cost + 1 + stone_weight
                    neighbors.append((
                        State(new_pos, new_stone_weights, push_cost),
                        push_char
                    ))

        return neighbors

    def solve_ucs(self) -> Tuple[List[str], Dict]:
        # time measurement
        start_time = time.time()
        start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

        initial_state = self.get_initial_state()
        pq = [(0, [], initial_state)]
        visited = set()
        
        while pq:
            cost, path, current_state = heapq.heappop(pq)

            if time.time() - start_time > time_out: # Terminate if timeout is exceeded
                print("Timeout reached. Exiting UCS.")
                end_time = time.time()
                end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024

                stats = {
                    'steps': len(path),
                    'weight': cost - len(path),
                    'nodes': self.nodes_generated,
                    'time': (end_time - start_time) * 1000,
                    'memory': end_memory - start_memory
                }
                return None, stats  
            
            if current_state in visited:
                continue
                
            visited.add(current_state)
            
            # Debug print
            # print(f"\nCurrent_state state (cost={cost}):")
            # print(self.print_state(current_state))
            
            if self.is_goal_state(current_state):
                end_time = time.time()
                end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                
                total_push_weight = cost - len(path)
                
                stats = {
                    'steps': len(path),
                    'weight': total_push_weight,
                    'nodes': self.nodes_generated,
                    'time': (end_time - start_time) * 1000,
                    'memory': end_memory - start_memory
                }
                return path, stats
            
            for next_state, move in self.get_neighbors(current_state):
                if next_state not in visited:
                    self.nodes_generated += 1
                    heapq.heappush(pq, (
                        next_state.cost,
                        path + [move],
                        next_state
                    ))
                    
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        stats = {
            'steps': len(path),
            'weight': cost - len(path),
            'nodes': self.nodes_generated,
            'time': (end_time - start_time) * 1000,
            'memory': end_memory - start_memory
        }
        return None, stats

def read_input(filepath: str) -> Tuple[List[int], List[str]]:
    with open(filepath, 'r') as f:
        stone_weights = list(map(int, f.readline().strip().split()))
        maze = [line.rstrip('\n') for line in f.readlines()]
    return stone_weights, maze

def write_output(filepath: str, solution: List[str], stats: Dict):
    with open(filepath, 'a') as f:
        f.write('UCS\n')
        f.write(f"Steps: {stats['steps']}, Weight: {stats['weight']}, " +
                f"Nodes: {stats['nodes']}, Time (ms): {stats['time']:.2f}, " +
                f"Memory (MB): {stats['memory']:.2f}\n")
        f.write(f"{''.join(solution)}\n")

def solve_maze(input_path: str, output_path: str):
    stone_weights, maze = read_input(input_path)
    solver = MazeSolver(maze, stone_weights)
    solution, stats = solver.solve_ucs()
    
    if solution:
        write_output(output_path, solution, stats)
    else:
        write_output(output_path, 'No solution', stats)

def main():
    for i in range(1, 11):
        input_file = f'Test_cases\\input-{i}.txt'
        output_file = f'Outputs\\output-{i}.txt'
        solve_maze(input_file, output_file)

if __name__ == "__main__":
    main()