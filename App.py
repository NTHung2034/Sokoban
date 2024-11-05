import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import os
from PIL import Image, ImageTk
from Algorithms import ucs, bfs, dfs, a_star
import copy

class SokobanGUI:
    def __init__(self, root, output_dir="Outputs"):
        self.root = root
        self.root.title("Sokoban Solver")
        self.root.set_theme("breeze") 
        self.root.minsize(1024, 768) 

        # GUI state variables
        self.current_step = 0
        self.is_playing = False
        self.animation_speed = 500
        self.current_maze = []
        self.initial_maze = []
        self.solution_path = ""
        self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
        self.output_dir = output_dir
        self.tile_size = 64
        self.tile_images = {}
        self.stone_weights = []
        self.total_weight_pushed = 0
        self.weight_history = []
        self.background_image = None
        self.starting_image = None
        self.missing_maze = []

        self.setup_gui()
        self.load_tileset()
        self.load_background()
    
    def load_starting_image(self):
        """Load and display the starting image"""
        try:
            # Load the starting picture
            self.starting_image = Image.open("./Tileset/starting_screen.png")

            # Check if the canvas has a valid size
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width > 0 and canvas_height > 0:
                # Resize the starting picture to fit the canvas
                self.starting_image = self.starting_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                self.starting_image_tk = ImageTk.PhotoImage(self.starting_image)

                # Set the starting picture as the background of the canvas
                self.canvas.create_image(0, 0, image=self.starting_image_tk, anchor="nw", tags="background")
                self.update_display()
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to load starting image: {str(e)}")
            self.starting_image_tk = None

    def load_background(self):
        """Load background image for the canvas"""
        try:
            bg_image = Image.open("./tileset/background.png")
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            bg_image = bg_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            self.background_image = ImageTk.PhotoImage(bg_image)
        except Exception as e:
            messagebox.showwarning("Warning", f"Failed to load background image: {str(e)}")
            self.background_image = None        
    
    def load_tileset(self):
        """Load and store tile images with proper resizing"""
        try:
            tileset_mapping = {
                '#': "wall.png",
                ' ': "free_space.png",
                '@': "ares.png",
                '$': "stone.png",
                '.': "switch.png",
                '*': "stone_on_switch.png",
                '+': "ares_on_switch.png"
            }
            for char, filename in tileset_mapping.items():
                image = Image.open(os.path.join("tileset", filename))
                image = image.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
                self.tile_images[char] = ImageTk.PhotoImage(image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tileset: {str(e)}")
            self.tile_images = {}

    def remake_maze(self): 
        begin_label = ttk.Label(self.root, text="Remaking missing mazes...")
        begin_label.grid(row=6, column=0)

        while self.missing_maze:
            maze = self.missing_maze.pop()
            bfs.remake_output(maze)
            dfs.remake_output(maze)
            ucs.remake_output(maze)
            a_star.remake_output(maze)

        begin_label.destroy()

        end_label = ttk.Label(self.root, text="Remaking missing mazes... Done!")
        end_label.grid(row=6, column=0)

        self.root.after(3000, end_label.destroy) # Remove the done label after 3 seconds

    def setup_gui(self):
        # Top control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0)

        # Algorithm selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=0, padx=5)
        self.algo_var = tk.StringVar(value="UCS")
        algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, 
                                  values=["BFS", "DFS", "UCS", "A*"], state="readonly")
        algo_combo.grid(row=0, column=1, padx=5)


        # Test case selection
        ttk.Label(control_frame, text="Test Case:").grid(row=0, column=2, padx=5)
        self.test_var = tk.StringVar(value="1")
        test_combo = ttk.Combobox(control_frame, textvariable=self.test_var, 
                                  values=[f"{i}" for i in range(1, 11)], state="readonly")
        test_combo.grid(row=0, column=3, padx=5)

        # Solve button
        ttk.Button(control_frame, text="Solve", command=self.solve_maze).grid(row=0, column=4, padx=5)

        # Remake button
        ttk.Button(control_frame, text="Remake", command=self.remake_maze).grid(row=0, column=5, padx=5)

        # Playback controls
        control_frame2 = ttk.Frame(self.root, padding="10")
        control_frame2.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Center the playback controls
        control_frame2.grid_columnconfigure(0, weight=1)
        control_frame2.grid_columnconfigure(6, weight=1)

        # Create a frame for the buttons to keep them centered
        buttons_frame = ttk.Frame(control_frame2)
        buttons_frame.grid(row=0, column=1, columnspan=4)

        # Buttons for playback
        ttk.Button(buttons_frame, text="⏮", command=self.reset_animation).pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="⏪", command=self.step_backward).pack(side=tk.LEFT, padx=2)
        self.play_button = ttk.Button(buttons_frame, text="▶", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(buttons_frame, text="⏩", command=self.step_forward).pack(side=tk.LEFT, padx=2)

        # Speed control
        speed_frame = ttk.Frame(control_frame2)
        speed_frame.grid(row=0, column=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT, padx=5)
        self.speed_scale = ttk.Scale(speed_frame, from_=1000, to=100, orient=tk.HORIZONTAL,
                                     command=self.update_speed)
        self.speed_scale.set(500)
        self.speed_scale.pack(side=tk.LEFT, padx=5)

        # Canvas frame with weight configuration
        canvas_frame = ttk.Frame(self.root, padding="10")
        canvas_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg=self.starting_image)
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure canvas frame grid weights
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.load_starting_image()

        # Stats frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="10")
        stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)

        # Stats labels
        self.stats_labels = {}
        stats = ["Steps", "Weight", "Nodes", "Time (ms)", "Memory (MB)"]
        for i, stat in enumerate(stats):
            ttk.Label(stats_frame, text=f"{stat}:").grid(row=0, column=i*2, padx=5)
            self.stats_labels[stat] = ttk.Label(stats_frame, text="0")
            self.stats_labels[stat].grid(row=0, column=i*2+1, padx=5)

        # Configure column weights to center the stats
        for i in range(len(stats) * 2):
            stats_frame.grid_columnconfigure(i, weight=1)
    
    def solve_maze(self):
        algo = self.algo_var.get()
        test_case = self.test_var.get()
        
        # Load initial maze state and stone weights
        maze_file = f"Test_cases/input-{test_case}.txt"
        try:
            with open(maze_file, 'r') as f:
                # First line contains stone weights
                weights = f.readline().strip().split()
                self.stone_weights = [int(w) for w in weights]
                # Rest of the lines contain the maze
                self.initial_maze = [list(line.strip()) for line in f.readlines()]
            self.current_maze = copy.deepcopy(self.initial_maze)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Test case file {maze_file} not found!")
            return

        output_file = os.path.join(self.output_dir, f"output-{test_case}.txt")
        if not os.path.exists(output_file):
            messagebox.showerror("Error", f"Output file {output_file} not found!")
            self.missing_maze.append(test_case) # test case for remake
            return 
        
        # Read output file
        try:
            with open(output_file, 'r') as f:
                lines = f.readlines()

            # Find the selected algorithm section
            algo_start = -1
            for i, line in enumerate(lines):
                if line.strip() == algo:
                    algo_start = i
                    break
            
            if algo_start == -1:
                messagebox.showerror("Error", f"Algorithm {algo} not found in output file!")
                return

            # Parse solution details
            stats_line = lines[algo_start + 1].strip()
            way = lines[algo_start + 2].strip()

            # Check if the second line contains "No solution"
            if "No solution" in way:
                # Parse the limited statistics available for no solution case
                try:
                    parts = stats_line.split(", ")
                    self.stats = {
                        "steps": 0,
                        "weight": 0,
                        "nodes": int(parts[2].split(": ")[1]),
                        "time": float(parts[3].split(": ")[1].replace('s', '')) * 1000 if 's' in parts[3] else float(parts[3].split(": ")[1]),
                        "memory": float(parts[4].split(": ")[1])
                    }
                except Exception as e:
                    print(f"Error parsing no solution statistics: {e}")
                    self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
                
                self.solution_path = ""
                messagebox.showinfo("Result", f"No solution found for {algo}")
                self.update_stats(no_solution=True)
                return

            # Regular solution case - parse all statistics and solution path
            try:
                # Parse statistics
                parts = stats_line.split(", ")
                self.stats["steps"] = int(parts[0].split(": ")[1])
                self.stats["weight"] = int(parts[1].split(": ")[1])
                self.stats["nodes"] = int(parts[2].split(": ")[1])
                
                # Handle time format (both 'seconds' and 'milliseconds')
                time_part = parts[3].split(": ")[1]
                if 's' in time_part:  # Format is in seconds
                    self.stats["time"] = float(time_part.replace('s', '')) * 1000  # Convert to ms
                else:  # Format is in milliseconds
                    self.stats["time"] = float(time_part)
                
                self.stats["memory"] = float(parts[4].split(": ")[1])
                
                # Get solution path
                self.solution_path = lines[algo_start + 2].strip()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse statistics: {str(e)}")
                return

            # Reset maze and update display
            self.current_step = 0
            self.reset_maze()
            self.update_display()
            self.update_stats()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse output file: {str(e)}")
            return
 
        self.total_weight_pushed = 0
        self.weight_history = []
        
        # After parsing solution path, precalculate weights for each step
        if self.solution_path and not "No solution" in self.solution_path:
            self.calculate_weight_history()

    def calculate_weight_history(self):
        """Precalculate weights for each step of the solution"""
        self.weight_history = [0]  # Start with 0 weight
        temp_maze = copy.deepcopy(self.initial_maze)
        
        # Create a map of stone positions to their weights
        stone_positions = {}
        stone_count = 0
        for i, row in enumerate(temp_maze):
            for j, cell in enumerate(row):
                if cell in ['$', '*']:
                    if stone_count < len(self.stone_weights):
                        stone_positions[(i, j)] = self.stone_weights[stone_count]
                        stone_count += 1

        # For each move in the solution
        for move in self.solution_path:
            last_weight = self.weight_history[-1]  # Get previous total weight
            
            if move.isupper():  # Box pushing move
                # Find player position
                player_pos = None
                for i, row in enumerate(temp_maze):
                    for j, cell in enumerate(row):
                        if cell in ['@', '+']:
                            player_pos = (i, j)
                            break
                    if player_pos:
                        break
                
                if player_pos:
                    # Calculate stone position based on direction
                    dr, dc = 0, 0
                    if move.upper() == 'U': dr = -1
                    elif move.upper() == 'D': dr = 1
                    elif move.upper() == 'L': dc = -1
                    elif move.upper() == 'R': dc = 1
                    
                    stone_pos = (player_pos[0] + dr, player_pos[1] + dc)
                    if stone_pos in stone_positions:
                        # Add weight of pushed stone to total
                        last_weight += stone_positions[stone_pos]
                        
                        # Update stone position in our tracking
                        new_stone_pos = (stone_pos[0] + dr, stone_pos[1] + dc)
                        stone_positions[new_stone_pos] = stone_positions[stone_pos]
                        del stone_positions[stone_pos]
                
            # Apply move to temp maze
            self.apply_move_to_maze(temp_maze, move)
            # Add the weight for this step
            self.weight_history.append(last_weight)

    def apply_move_to_maze(self, maze, move):
        """Helper function to apply move to a maze without affecting display"""
        player_pos = None
        for i, row in enumerate(maze):
            for j, cell in enumerate(row):
                if cell in ['@', '+']:
                    player_pos = (i, j)
                    break
            if player_pos:
                break
                
        if not player_pos:
            return False
            
        row, col = player_pos
        dr, dc = 0, 0
        
        if move.lower() == 'u': dr = -1
        elif move.lower() == 'd': dr = 1
        elif move.lower() == 'l': dc = -1
        elif move.lower() == 'r': dc = 1
        
        new_row, new_col = row + dr, col + dc
        
        if (new_row < 0 or new_row >= len(maze) or new_col < 0 or new_col >= len(maze[0])):
            return False
            
        current_cell = maze[row][col]
        target_cell = maze[new_row][new_col]
        player_on_switch = current_cell == '+'
        
        if target_cell == '#':
            return False
            
        if move.isupper() and target_cell in ['$', '*']:
            box_row, box_col = new_row + dr, new_col + dc
            
            if (0 <= box_row < len(maze) and 
                0 <= box_col < len(maze[0])):
                
                box_target = maze[box_row][box_col]
                
                if box_target in [' ', '.']:
                    maze[box_row][box_col] = '*' if box_target == '.' else '$'
                    maze[new_row][new_col] = '+' if target_cell == '*' else '@'
                    maze[row][col] = '.' if player_on_switch else ' '
                    return True
            return False
            
        elif move.islower():
            if target_cell in ['$', '*']:
                return False
                
            if target_cell in [' ', '.']:
                maze[new_row][new_col] = '+' if target_cell == '.' else '@'
                maze[row][col] = '.' if player_on_switch else ' '
                return True
                
        return False       

    def update_display(self): 
        if not self.current_maze:
            return
            
        self.canvas.delete("all")
        
        # Calculate maze dimensions
        maze_height = len(self.current_maze) * self.tile_size
        maze_width = len(self.current_maze[0]) * self.tile_size
        
        # Get current canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Calculate centering offsets
        offset_x = max(0, (canvas_width - maze_width) // 2)
        offset_y = max(0, (canvas_height - maze_height) // 2)
        
        # Set scrollable area to be at least as large as the canvas
        scroll_width = max(canvas_width, maze_width + offset_x * 2)
        scroll_height = max(canvas_height, maze_height + offset_y * 2)
        self.canvas.config(scrollregion=(0, 0, scroll_width, scroll_height))

        # # Draw background if available
        # if self.background_image:
        #     bg_width = self.background_image.width()
        #     bg_height = self.background_image.height()
            
        #     # Fill entire visible area with background
        #     for y in range(0, scroll_height, bg_height):
        #         for x in range(0, scroll_width, bg_width):
        #             self.canvas.create_image(x, y, image=self.background_image, anchor="nw")
        
        # Draw full-size background image
        if self.background_image:
            self.canvas.create_image(0, 0, image=self.background_image, anchor="nw", tags="background")
                
        # Draw the maze tiles with offset
        for i, row in enumerate(self.current_maze):
            for j, cell in enumerate(row):
                x = offset_x + j * self.tile_size
                y = offset_y + i * self.tile_size
                
                if cell in self.tile_images:
                    self.canvas.create_image(x, y, image=self.tile_images[cell], anchor="nw")
                else:
                    colors = {
                        '#': 'gray',
                        ' ': '',
                        '@': 'yellow',
                        '$': 'brown',
                        '.': 'lightgreen',
                        '*': 'green',
                        '+': 'orange'
                    }
                    color = colors.get(cell)
                    if color:
                        self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                                  fill=color, outline='black')
    
    def on_resize(self, event):
        self.load_background()
        self.load_starting_image()
        self.update_display()   

    def update_stats(self, no_solution=False):
        if no_solution:
            self.stats_labels["Steps"].config(text="No solution")
            self.stats_labels["Weight"].config(text="0")
            # Still show the available statistics
            self.stats_labels["Nodes"].config(text=f"{self.stats['nodes']}")
            self.stats_labels["Time (ms)"].config(text=f"{self.stats['time']:.2f}")
            self.stats_labels["Memory (MB)"].config(text=f"{self.stats['memory']:.2f}")
        else:
            self.stats_labels["Steps"].config(text=f"{self.current_step}/{self.stats['steps']}")
            self.stats_labels["Weight"].config(text=f"{self.total_weight_pushed}/{self.stats['weight']}")
            self.stats_labels["Nodes"].config(text=f"{self.stats['nodes']}")
            self.stats_labels["Time (ms)"].config(text=f"{self.stats['time']:.2f}")
            self.stats_labels["Memory (MB)"].config(text=f"{self.stats['memory']:.2f}")    

    def find_player_pos(self, maze):
        for i, row in enumerate(maze):
            for j, cell in enumerate(row):
                if cell in ['@', '+']:
                    return i, j
        return None
    
    def reset_animation(self):
        self.is_playing = False
        self.play_button.config(text="▶")
        self.current_step = 0
        self.reset_maze()
        self.update_display()
        self.update_stats()

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸" if self.is_playing else "▶")
        if self.is_playing:
            self.play_animation()

    def update_speed(self, value):
        self.animation_speed = int(float(value))
    
    def reset_maze(self):
        self.current_maze = copy.deepcopy(self.initial_maze)

    def apply_move(self, move):
        """Improved move application with better box pushing logic"""
        player_pos = self.find_player_pos(self.current_maze)
        if not player_pos:
            return False
        
        row, col = player_pos
        dr, dc = 0, 0
        
        # Determine direction of movement
        if move.lower() == 'u': dr = -1
        elif move.lower() == 'd': dr = 1
        elif move.lower() == 'l': dc = -1
        elif move.lower() == 'r': dc = 1
        else:
            return False  # Invalid move
        
        new_row, new_col = row + dr, col + dc
        
        # Check bounds
        if (new_row < 0 or new_row >= len(self.current_maze) or
            new_col < 0 or new_col >= len(self.current_maze[0])):
            return False
        
        # Get current cell states
        current_cell = self.current_maze[row][col]
        target_cell = self.current_maze[new_row][new_col]
        
        # Player is on switch?
        player_on_switch = current_cell == '+'
        
        # Handle wall collision
        if target_cell == '#':
            return False
            
        # Handle box pushing (uppercase moves)
        if move.isupper() and target_cell in ['$', '*']:
            box_row, box_col = new_row + dr, new_col + dc
            
            # Check box push validity
            if (0 <= box_row < len(self.current_maze) and 
                0 <= box_col < len(self.current_maze[0])):
                
                box_target = self.current_maze[box_row][box_col]
                
                # Can only push into empty space or switch
                if box_target in [' ', '.']:
                    # Update box position
                    self.current_maze[box_row][box_col] = '*' if box_target == '.' else '$'
                    # Update player position
                    self.current_maze[new_row][new_col] = '+' if target_cell == '*' else '@'
                    # Update previous player position
                    self.current_maze[row][col] = '.' if player_on_switch else ' '
                    return True
            return False
            
        # Handle regular movement (lowercase moves)
        elif move.islower():
            # Can't walk through boxes with lowercase moves
            if target_cell in ['$', '*']:
                return False
                
            # Move to empty space or switch
            if target_cell in [' ', '.']:
                self.current_maze[new_row][new_col] = '+' if target_cell == '.' else '@'
                self.current_maze[row][col] = '.' if player_on_switch else ' '
                return True
                
        return False

    def step_forward(self):
        """Updated step forward with correct weight tracking"""
        if not self.solution_path or self.current_step >= len(self.solution_path):
            self.is_playing = False
            self.play_button.config(text="▶")
            return False
                
        move = self.solution_path[self.current_step]
        if self.apply_move(move):
            self.current_step += 1
            # Update total weight from precalculated history
            if self.weight_history and self.current_step < len(self.weight_history):
                self.total_weight_pushed = self.weight_history[self.current_step]
            self.update_display()
            self.update_stats()
            return True
        return False

    def play_animation(self):
        """Improved animation with better error handling"""
        if self.is_playing:
            if self.step_forward():
                self.root.after(self.animation_speed, self.play_animation)
            else:
                self.is_playing = False
                self.play_button.config(text="▶")
   
    def step_backward(self):
        """Updated step backward with correct weight tracking"""
        if self.current_step <= 0:
            return
                
        self.current_step -= 1
        # Update total weight from precalculated history
        if self.weight_history and self.current_step < len(self.weight_history):
            self.total_weight_pushed = self.weight_history[self.current_step]
        else:
            self.total_weight_pushed = 0
            
        self.reset_maze()
        
        # Replay all moves up to current step
        for i in range(self.current_step):
            move = self.solution_path[i]
            if not self.apply_move(move):
                print(f"Failed to replay move: {move} at step {i}")
                break
                    
        self.update_display()
        self.update_stats()
    
    def reset_animation(self):
        self.is_playing = False
        self.play_button.config(text="▶")
        self.current_step = 0
        self.reset_maze()
        self.update_display()
        self.update_stats()

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.play_button.config(text="⏸" if self.is_playing else "▶")
        if self.is_playing:
            self.play_animation()

def main():
    root = ThemedTk()
    app = SokobanGUI(root)
    root.bind('<Configure>', app.on_resize)
    root.mainloop()

if __name__ == "__main__":
    main()