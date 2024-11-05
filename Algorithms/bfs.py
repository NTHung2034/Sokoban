import time
import psutil
from collections import deque, namedtuple

# Define directions and their actions
DIRECTIONS = {'u': (-1, 0), 'd': (1, 0), 'l': (0, -1), 'r': (0, 1)}
PUSH_DIRECTIONS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

# Define the State structure
State = namedtuple("State", ["ares_pos", "stones", "path", "steps", "weight"])

class MazeSolver:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.parse_input()

    def parse_input(self):
        with open(self.input_file, 'r') as f:
            # Parse weights
            self.stone_weights = list(map(int, f.readline().strip().split()))

            # Parse the grid
            self.grid = []
            for line in f:
                if line.strip():  # Bỏ qua dòng trống nếu có
                    self.grid.append(list(line.rstrip()))

            # Lấy kích thước thực tế của lưới
            self.n = len(self.grid)
            self.m = max(len(row) for row in self.grid) if self.grid else 0

        # Khởi tạo danh sách và tập hợp cho các đối tượng
        self.stones = []
        self.switches = set()
        self.ares_pos = None

        # Duyệt qua từng hàng và cột trong lưới
        for i in range(self.n):
            for j in range(len(self.grid[i])):  # Sử dụng độ dài thực tế của dòng `i`
                if self.grid[i][j] == '@':
                    self.ares_pos = (i, j)
                elif self.grid[i][j] == '$':
                    self.stones.append((i, j))
                elif self.grid[i][j] == '.':
                    self.switches.add((i, j))
                elif self.grid[i][j] == '*':
                    self.switches.add((i, j))
                    self.stones.append((i, j))
        
    def bfs(self):
        start_time = time.time()
        initial_state = State(self.ares_pos, tuple(self.stones), '', 0, 0)
        queue = deque([initial_state])
        visited = set()
        visited.add((initial_state.ares_pos, initial_state.stones))
        nodes_generated = 1

        while queue:
             # Check for timeout
            time_out = 60 # 60 giây
            if time.time() - start_time > time_out:
                state = state._replace(path="No solution\n")
                return self.generate_output(state, nodes_generated, start_time)  # Terminate if timeout is exceeded
            
            state = queue.popleft()
            if self.is_goal(state):
                return self.generate_output(state, nodes_generated, start_time)

            # Try moving in each direction
            for move, (dx, dy) in DIRECTIONS.items():
                new_ares_pos = (state.ares_pos[0] + dx, state.ares_pos[1] + dy)
                
                # Normal movement check
                if self.is_valid_move(new_ares_pos, state.stones):
                    new_state = State(new_ares_pos, state.stones, state.path + move, state.steps + 1, state.weight)
                    if (new_state.ares_pos, new_state.stones) not in visited:
                        queue.append(new_state)
                        visited.add((new_state.ares_pos, new_state.stones))
                        nodes_generated += 1

                # Try pushing stones if Ares is on a stone
                if new_ares_pos in state.stones:
                    push_dir = move.upper()  # Convert move to upper case for pushing
                    new_stone_pos = (new_ares_pos[0] + dx, new_ares_pos[1] + dy)

                    # Valid push check
                    if self.is_valid_push(new_ares_pos, new_stone_pos, state.stones):
                        stone_index = state.stones.index(new_ares_pos)
                        new_stones = list(state.stones)
                        new_stones[stone_index] = new_stone_pos
                        new_weight = state.weight + self.stone_weights[stone_index]
                        new_state = State(new_ares_pos, tuple(new_stones), state.path + push_dir, state.steps + 1, new_weight)

                        if (new_state.ares_pos, new_state.stones) not in visited:
                            queue.append(new_state)
                            visited.add((new_state.ares_pos, new_state.stones))
                            nodes_generated += 1

                            # Kiểm tra mục tiêu sau khi đẩy
                            if self.is_goal(new_state):
                                return self.generate_output(new_state, nodes_generated, start_time)
                            
        state = state._replace(path="No solution")
        return self.generate_output(state, nodes_generated, start_time)   # No solution found

    def is_goal(self, state):
        # Kiểm tra tất cả các vị trí stone hiện tại có nằm trên các switch không
        return all(stone in self.switches for stone in state.stones)

    def is_valid_move(self, pos, stones):
        x, y = pos
        return 0 <= x < self.n and 0 <= y < self.m and self.grid[x][y] != '#' and pos not in stones

    def is_valid_push(self, pos, new_pos, stones):
        x, y = new_pos
        return 0 <= x < self.n and 0 <= y < self.m and self.grid[x][y] != '#' and new_pos not in stones

    def generate_output(self, final_state, nodes_generated, start_time):
        elapsed_time = time.time() - start_time
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        output_content = [
            "BFS",
            f"Steps: {final_state.steps}, Weight: {final_state.weight}, Nodes: {nodes_generated}, "
            f"Time (ms): {elapsed_time * 1000:.2f}, Memory (MB): {memory_usage:.2f}",
            f"{final_state.path}\n"
        ]
        with open(self.output_file, 'a') as f:
            f.write("\n".join(output_content))

def remake_output(test_case):
    input_file = f'Test_cases\\input-{test_case}.txt'
    output_file = f'Outputs\\output-{test_case}.txt'
    solver = MazeSolver(input_file, output_file)
    solver.bfs()

def main():
     for i in range(1, 11):
        input_file = f'Test_cases\\input-{i}.txt'
        output_file = f'Outputs\\output-{i}.txt'
        solver = MazeSolver(input_file, output_file)
        solver.bfs()

if __name__ == "__main__":
    main()
   