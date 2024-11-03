import time
import heapq
import psutil
from abc import ABC, abstractmethod

# class Node: define a node in the search tree
#=======================================================================================================
#=========================================== BEGIN CLASS: NODE =========================================
class Node:
    def __init__(self, ares_position=None, boxes=None, grid=None, g=0, h=None, parent=None, action=None, search_time=0):
        self.ares_position = ares_position
        self.boxes = boxes if boxes is not None else []
        self.grid = grid
        self.g = g
        self.h = h if h is not None else 0
        self.parent = parent
        self.action = action
        self.search_time = search_time

    @property
    def f(self):
        """the function to calculate the total cost of the node (heuristic + cost)"""
        return self.g + self.h

    def __eq__(self, other):
        """the function to compare two nodes"""
        return self.ares_position == other.ares_position and self.boxes == other.boxes

    def __hash__(self):
        """the function to hash a node"""
        return hash((self.ares_position, tuple(self.boxes)))

    def __lt__(self, other):
        """the function to compare two nodes"""
        return self.f < other.f

    def get_path(self):
        """the function to get the path from the root node to the current node"""
        path = []
        node = self

        # get the path from the root node to the current node (backward)
        while node.parent:
            path.append(node.action)
            node = node.parent
        path.reverse()
        return ''.join(path)
#=======================================================================================================
#=========================================== END CLASS: NODE =========================================== 

# class A_Star_Search: define the A* search algorithm
#=======================================================================================================
#=========================================== BEGIN CLASS: A_Star_Search ================================ 
class A_Star_Search:
    def __init__(self, initial_state, goals, weights):
        self.initial_state = initial_state
        self.goals = goals
        self.weights = weights
        self.open_list = []
        self.closed_list = set()
        self.nodes_generated = 0
        self.memory_used = 0

    def search(self):
        """the search function"""

        process = psutil.Process()  # begin to monitor the memory usage
        start_time = time.time()  # begin to monitor the time
        initial_node = self.initial_state
        initial_node.h = self.heuristic(initial_node)

        # push the initial node to the open list
        heapq.heappush(self.open_list, (initial_node.f, initial_node))

        # maximum allowed search time in seconds (1 minute 30 seconds)
        max_time = 60

        # begin the search loop
        while self.open_list:
            # check if the elapsed time has exceeded the maximum time
            current_time = time.time()
            if current_time - start_time > max_time:
                search_time = current_time - start_time
                self.memory_used = process.memory_info().rss / (1024 * 1024)  # get the memory usage in MB
                print("Time limit exceeded. No solution found.")
                return None, search_time

            # pop the node with the smallest f value from the open list
            _, current_node = heapq.heappop(self.open_list)
            self.closed_list.add(current_node)

            # check if the current node is a goal node
            if self.is_goal(current_node):
                end_time = time.time()  
                search_time = end_time - start_time
                self.memory_used = process.memory_info().rss / (1024 * 1024)  # get the memory usage in MB
                solution = self.reconstruct_path(current_node)
                
                # return the solution and the search time
                return solution, search_time 

            # expand the current node
            neighbors = self.get_neighbors(current_node)

            # add the neighbors to the open list if can be expanded
            for neighbor in neighbors:
                if neighbor not in self.closed_list and not self.is_deadlock(neighbor):
                    neighbor.g = current_node.g + 1
                    neighbor.h = self.heuristic(neighbor)

                    heapq.heappush(self.open_list, (neighbor.f, neighbor))
                    self.nodes_generated += 1

        # return None if no solution is found
        end_time = time.time()
        return None, end_time - start_time

    def get_neighbors(self, node):
        """the function to get the neighbors of a node"""

        neighbors = []
        directions = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}

        for action, (dx, dy) in directions.items():
            new_ares_pos = (node.ares_position[0] + dx, node.ares_position[1] + dy)

            # Check if Ares can move to the new position
            if self.is_valid_move(node, new_ares_pos):
                new_grid = [row[:] for row in node.grid]
                
                # Update the old position
                if node.grid[node.ares_position[0]][node.ares_position[1]] == '+':
                    new_grid[node.ares_position[0]][node.ares_position[1]] = '.'  # Ares leaving a goal
                else:
                    new_grid[node.ares_position[0]][node.ares_position[1]] = ' '  # Ares leaving an empty space

                # Update the new position
                if new_grid[new_ares_pos[0]][new_ares_pos[1]] == '.':
                    new_grid[new_ares_pos[0]][new_ares_pos[1]] = '+'  # Ares moves onto a goal
                else:
                    new_grid[new_ares_pos[0]][new_ares_pos[1]] = '@'  # Ares moves to an empty space

                new_node = Node(
                    g=node.g + 1,
                    h=self.heuristic(node),
                    ares_position=new_ares_pos,
                    boxes=node.boxes[:],
                    grid=new_grid,
                    parent=node,
                    action=action
                )
                neighbors.append(new_node)

            # Check if Ares can push a stone
            elif self.is_pushable(node, new_ares_pos, dx, dy):
                next_pos = (new_ares_pos[0] + dx, new_ares_pos[1] + dy)
                if self.is_valid_move(node, next_pos):
                    new_boxes = [next_pos if box == new_ares_pos else box for box in node.boxes]
                    new_grid = [row[:] for row in node.grid]
                    
                    # Update Ares' old position
                    if node.grid[node.ares_position[0]][node.ares_position[1]] == '+':
                        new_grid[node.ares_position[0]][node.ares_position[1]] = '.'
                    else:
                        new_grid[node.ares_position[0]][node.ares_position[1]] = ' '

                    # Update stone's old position and Ares' new position
                    if new_grid[new_ares_pos[0]][new_ares_pos[1]] == '*':
                        new_grid[new_ares_pos[0]][new_ares_pos[1]] = '+'  # Ares moves to goal after pushing stone
                    else:
                        new_grid[new_ares_pos[0]][new_ares_pos[1]] = '@'  # Ares moves to empty space after pushing stone

                    # Update stone's new position
                    if new_grid[next_pos[0]][next_pos[1]] == '.':
                        new_grid[next_pos[0]][next_pos[1]] = '*'  # Stone moves to goal
                    else:
                        new_grid[next_pos[0]][next_pos[1]] = '$'  # Stone moves to empty space

                    new_node = Node(
                        g=node.g + 1,
                        h=self.heuristic(node),
                        ares_position=new_ares_pos,
                        boxes=new_boxes,
                        grid=new_grid,
                        parent=node,
                        action=action.upper()
                    )
                    neighbors.append(new_node)

        return neighbors

    def is_valid_position(self, position, grid):
        """the function to check if a position is valid"""

        rows, cols = len(grid), len(grid[0])
        row, col = position
        return 0 <= row < rows and 0 <= col < cols and grid[row][col] != '#'

    def is_deadlock(self, node):
        """the function to check if a node is a deadlock"""

        for box in node.boxes:
            if not self.is_valid_position(box, node.grid):
                return True
            if self.is_cornered(box, node.grid) and box not in self.goals:
                return True
        return False

    def is_cornered(self, box, grid):
        """Check if a box is cornered"""

        x, y = box
        if (grid[x-1][y] == '#' or grid[x+1][y] == '#') and (grid[x][y-1] == '#' or grid[x][y+1] == '#'):
            return True
        return False

    def is_goal(self, node):
        """the function to check if a node is a goal"""
        return all(box in self.goals for box in node.boxes)

    def reconstruct_path(self, node):
        """the function to reconstruct the path from the root node to the current node"""

        path = []
        while node:
            path.append(node)
            node = node.parent
        return path[::-1]

    def print_result(self, solution, steps, search_time):
        """the function to print the result"""

        print(f"Solution found in {steps} steps and {search_time:.2f} seconds.")
        print(f"Total weight pushed: {self.total_weight}")
        print(f"Memory used: {self.memory_used:.2f} KB")
        for step in solution:
            print(step)
        return solution

    def is_pushable(self, node, pos, dx, dy):
        """the function to check if a stone is pushable"""

        next_pos = (pos[0] + dx, pos[1] + dy)
        return pos in node.boxes and self.is_valid_move(node, next_pos)

    def is_valid_move(self, node, pos):
        """the function to check if a move is valid"""

        return node.grid[pos[0]][pos[1]] in [' ', '.']


    def heuristic(self, node):
        """the function to calculate the heuristic value of a node"""

        total_distance = 0
        for box in node.boxes:
            min_distance = min(abs(box[0] - goal[0]) + abs(box[1] - goal[1]) for goal in self.goals)
            total_distance += min_distance * self.weights[node.boxes.index(box)]
        return total_distance
#=======================================================================================================
#=========================================== END CLASS: A_Star_Search ==================================   


#=======================================================================================================
#=========================================== GLOBAL FUNCTION  ==========================================
def read_input_file(filename):
    """the function to read the input file"""

    with open(filename, 'r') as file:
        weights = list(map(int, file.readline().strip().split()))
        grid = [list(line.strip()) for line in file]
    return weights, grid

def write_output_file(filename, algorithm_name, steps, total_weight, nodes_generated, search_time, memory_used, actions):
    """the function to write the output file"""

    with open(filename, 'a') as file:
        file.write(f"{algorithm_name}\n")
        file.write(f"Steps: {steps}, Weight: {total_weight}, Nodes: {nodes_generated}, Time (ms): {search_time:.2f}, Memory (MB): {memory_used:.2f}\n")
        file.write(f"{actions}\n")

def print_result(actions, steps, search_time, goals):
    """the function to print the result"""

    print(f"Solution found in {steps} steps and {search_time:.2f} seconds.")
    print("Actions:")
    for i, step in enumerate(actions):
        print(f"{i + 1}. {step}")

def create_initial_state(grid):
    """the function to create the initial state"""

    ares_position = None
    stone_positions = []
    goals = []

    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if grid[row][col] in ['@', '+']:
                ares_position = (row, col)
            if grid[row][col] in ['$','*']:
                stone_positions.append((row, col))
            if grid[row][col] in ['.', '*', '+']:
                goals.append((row, col))
    
    return ares_position, stone_positions, goals


def move_position(x, y, direction):
    """the function to move the position"""

    if direction == 'u':
        return x - 1, y
    elif direction == 'd':
        return x + 1, y
    elif direction == 'l':
        return x, y - 1
    elif direction == 'r':
        return x, y + 1
    return x, y

def calculate_total_cost(final_path, ares_position, stone_weights, stones):
    """the function to calculate the total cost of the solution"""

    total_cost = 0
    current_x, current_y = ares_position 
    stone_positions = stones.copy()  

    for action in final_path:
        # if the action is a move action
        if action in ['u', 'd', 'l', 'r']:  
            new_x, new_y = move_position(current_x, current_y, action)
        #     total_cost += 1  
            current_x, current_y = new_x, new_y  
        
        # if the action is a push action
        if action in ['U', 'D', 'L', 'R']:
            # get the direction of the stone 
            stone_direction = action.lower()  
            stone_x, stone_y = move_position(current_x, current_y, stone_direction) 
            
            # get the weight of the stone
            stone_weight = stone_weights[stone_positions.index((stone_x, stone_y))]
            total_cost +=  stone_weight  
            
            # update the position of the stone
            new_stone_x, new_stone_y = move_position(stone_x, stone_y, stone_direction)
            stone_positions[stone_positions.index((stone_x, stone_y))] = (new_stone_x, new_stone_y)

            # update the position of Ares
            current_x, current_y = stone_x, stone_y

    return total_cost


def main():
    for i in range(1, 11):
        # print(i)
        input_filename = f'Test_cases/input-{i}.txt'
        output_filename = f'Outputs/output-{i}.txt'
        weights, grid = read_input_file(input_filename)
        
        ares_position, stone_positions, goals = create_initial_state(grid)
        initial_node = Node(ares_position=ares_position, boxes=stone_positions, grid=grid)
        
        search_algorithm = A_Star_Search(initial_node, goals, weights)
        solution_node, search_time = search_algorithm.search()  
        
        if solution_node is not None:
            final_node = solution_node[-1]  
            steps = final_node.g
            total_weight = calculate_total_cost(final_node.get_path(), ares_position, weights, stone_positions)
            actions = final_node.get_path() 
             
        else:
            actions = "No solution"
            steps = 0
            total_weight = 0

        search_time = search_time * 1000 
        # print_result(actions, steps, search_time, goals) # print the result to the console

        print(f"output_{i}.txt")
        write_output_file(output_filename, "A*", steps, total_weight, search_algorithm.nodes_generated, search_time, search_algorithm.memory_used, actions)

if __name__ == "__main__":
    main()