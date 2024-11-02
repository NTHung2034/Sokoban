import tkinter as tk
from tkinter import ttk, messagebox
import os
from PIL import Image, ImageTk
import copy

class SokobanGUI:
    def __init__(self, root, output_dir="Outputs"):
        self.root = root
        self.root.title("Sokoban Solver")
        
        # GUI state variables
        self.current_step = 0
        self.is_playing = False
        self.animation_speed = 500  # milliseconds
        self.current_maze = []
        self.initial_maze = []
        self.solution_path = ""
        self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
        self.output_dir = output_dir
        self.tile_size = 32  # Size of tiles in pixels
        self.tile_images = {}
        
        # Load tileset
        self.load_tileset()
        
        # Setup GUI components
        self.setup_gui()
        
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
                # Resize image to match tile_size
                image = image.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
                self.tile_images[char] = ImageTk.PhotoImage(image)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tileset: {str(e)}")
            # Fallback to colored rectangles if tileset loading fails
            self.tile_images = {}
    
    def setup_gui(self):
        # Top control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Algorithm selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=0, padx=5)
        self.algo_var = tk.StringVar(value="UCS")
        algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, 
                                  values=["UCS", "BFS", "DFS"], state="readonly")
        algo_combo.grid(row=0, column=1, padx=5)
        
        # Test case selection
        ttk.Label(control_frame, text="Test Case:").grid(row=0, column=2, padx=5)
        self.test_var = tk.StringVar(value="1")
        test_combo = ttk.Combobox(control_frame, textvariable=self.test_var,
                                  values=[f"{i}" for i in range(1, 11)], state="readonly")
        test_combo.grid(row=0, column=3, padx=5)
        
        # Solve button
        ttk.Button(control_frame, text="Solve", command=self.solve_maze).grid(row=0, column=4, padx=5)
        
        # Playback controls
        control_frame2 = ttk.Frame(self.root, padding="10")
        control_frame2.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame2, text="⏮", command=self.reset_animation).grid(row=0, column=0, padx=2)
        ttk.Button(control_frame2, text="⏪", command=self.step_backward).grid(row=0, column=1, padx=2)
        self.play_button = ttk.Button(control_frame2, text="▶", command=self.toggle_play)
        self.play_button.grid(row=0, column=2, padx=2)
        ttk.Button(control_frame2, text="⏩", command=self.step_forward).grid(row=0, column=3, padx=2)
        
        # Speed control
        ttk.Label(control_frame2, text="Speed:").grid(row=0, column=4, padx=5)
        self.speed_scale = ttk.Scale(control_frame2, from_=100, to=1000, orient=tk.HORIZONTAL,
                                     command=self.update_speed)
        self.speed_scale.set(500)
        self.speed_scale.grid(row=0, column=5, padx=5)
        
        # Maze canvas - make it scrollable
        canvas_frame = ttk.Frame(self.root, padding="10")
        canvas_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create scrollbars
        self.h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        self.v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        self.canvas = tk.Canvas(canvas_frame, width=500, height=500, 
                              xscrollcommand=self.h_scrollbar.set,
                              yscrollcommand=self.v_scrollbar.set,
                              bg='white')
        
        # Configure scrollbars
        self.h_scrollbar.config(command=self.canvas.xview)
        self.v_scrollbar.config(command=self.canvas.yview)
        
        # Grid layout with scrollbars
        self.canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.h_scrollbar.grid(row=1, column=0, sticky=(tk.E, tk.W))
        self.v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Make canvas expandable
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
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
    
    def solve_maze(self):
        algo = self.algo_var.get()
        test_case = self.test_var.get()
        
        # Load initial maze state
        maze_file = f"Test_cases/input-{test_case}.txt"
        try:
            with open(maze_file, 'r') as f:
                self.initial_maze = [list(line.strip()) for line in f.readlines()]
            self.current_maze = copy.deepcopy(self.initial_maze)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Test case file {maze_file} not found!")
            return

        output_file = os.path.join(self.output_dir, f"output-{test_case}.txt")
        if not os.path.exists(output_file):
            messagebox.showerror("Error", f"Output file {output_file} not found!")
            return
        
        # Read output file
        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Find the relevant algorithm section
        algo_index = -1
        for i, line in enumerate(lines):
            if line.strip() == algo:
                algo_index = i
                break
                
        if algo_index == -1:
            messagebox.showerror("Error", f"Algorithm {algo} not found in output file!")
            return

        # Parse solution details
        stats_line = lines[algo_index + 1].strip()
        if "No solution" in stats_line:
            self.solution_path = ""
            self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
            messagebox.showinfo("Result", "No solution found for the selected algorithm.")
            self.update_stats(no_solution=True)
            return

        # Parse the solution path - ensure we get the complete path
        self.solution_path = lines[algo_index + 2].strip()
        
        # Parse statistics
        try:
            parts = stats_line.split(", ")
            self.stats["steps"] = int(parts[0].split(": ")[1])
            self.stats["weight"] = int(parts[1].split(": ")[1])
            self.stats["nodes"] = int(parts[2].split(": ")[1])
            self.stats["time"] = float(parts[3].split(": ")[1])
            self.stats["memory"] = float(parts[4].split(": ")[1])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse statistics: {str(e)}")
            return

        # Reset maze and update display
        self.current_step = 0
        self.reset_maze()
        self.update_display()
        self.update_stats()
    
    def update_display(self):
        if not self.current_maze:
            return
            
        self.canvas.delete("all")
        
        # Calculate total size needed
        total_height = len(self.current_maze) * self.tile_size
        total_width = len(self.current_maze[0]) * self.tile_size
        
        # Configure canvas scrolling region
        self.canvas.config(scrollregion=(0, 0, total_width, total_height))
        
        # Draw the maze
        for i, row in enumerate(self.current_maze):
            for j, cell in enumerate(row):
                x = j * self.tile_size
                y = i * self.tile_size
                
                # Draw tile image if available, otherwise fall back to colored rectangle
                if cell in self.tile_images:
                    self.canvas.create_image(x, y, image=self.tile_images[cell], anchor="nw")
                else:
                    # Fallback colors if images are not available
                    colors = {
                        '#': 'gray',
                        ' ': 'white',
                        '@': 'yellow',
                        '$': 'brown',
                        '.': 'lightgreen',
                        '*': 'green',
                        '+': 'orange'
                    }
                    color = colors.get(cell, 'white')
                    self.canvas.create_rectangle(x, y, x + self.tile_size, y + self.tile_size,
                                              fill=color, outline='black')

    def update_stats(self, no_solution=False):
        if no_solution:
            for label in self.stats_labels.values():
                label.config(text="N/A")
            self.stats_labels["Steps"].config(text="No solution")
        else:
            self.stats_labels["Steps"].config(text=f"{self.current_step}/{self.stats['steps']}")
            self.stats_labels["Weight"].config(text=f"{self.stats['weight']}")
            self.stats_labels["Nodes"].config(text=f"{self.stats['nodes']}")
            self.stats_labels["Time (ms)"].config(text=f"{self.stats['time']:.2f}")
            self.stats_labels["Memory (MB)"].config(text=f"{self.stats['memory']:.2f}")
    
    def find_player_pos(self, maze):
        for i, row in enumerate(maze):
            for j, cell in enumerate(row):
                if cell in ['@', '+']:
                    return i, j
        return None
    
    def step_forward(self):
        if not self.solution_path or self.current_step >= len(self.solution_path):
            return
            
        move = self.solution_path[self.current_step]
        self.apply_move(move)
        self.current_step += 1
        self.update_display()
        self.update_stats()
    
    def step_backward(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.reset_maze()
            for i in range(self.current_step):
                move = self.solution_path[i]
                self.apply_move(move)
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

    def play_animation(self):
        if self.is_playing and self.current_step < len(self.solution_path):
            self.step_forward()
            self.root.after(self.animation_speed, self.play_animation)
        else:
            self.is_playing = False
            self.play_button.config(text="▶")
    
    def update_speed(self, value):
        self.animation_speed = int(float(value))
    
    def reset_maze(self):
        self.current_maze = copy.deepcopy(self.initial_maze)

    def apply_move(self, move):
        player_pos = self.find_player_pos(self.current_maze)
        if not player_pos:
            return
        
        row, col = player_pos
        dr, dc = 0, 0
        
        # Determine direction of movement
        if move.lower() == 'u': dr = -1
        elif move.lower() == 'd': dr = 1
        elif move.lower() == 'l': dc = -1
        elif move.lower() == 'r': dc = 1
        
        new_row, new_col = row + dr, col + dc
        
        # Check if move is within bounds
        if (new_row < 0 or new_row >= len(self.current_maze) or
            new_col < 0 or new_col >= len(self.current_maze[0])):
            return
        
        # Get current cell type and target cell type
        current = self.current_maze[row][col]
        target = self.current_maze[new_row][new_col]
        
        # Handle pushing box (uppercase moves)
        if move.isupper():
            if target in ['$', '*']:
                box_row, box_col = new_row + dr
                box_row, box_col = new_row + dr, new_col + dc
                
                # Check if the box can be pushed
                if (box_row < 0 or box_row >= len(self.current_maze) or
                    box_col < 0 or box_col >= len(self.current_maze[0])):
                    return  # Box cannot be pushed out of bounds

                # Check the target cell of the box
                target_box = self.current_maze[box_row][box_col]
                if target_box in [' ', '.']:  # Space or switch
                    # Move the box
                    self.current_maze[box_row][box_col] = '$' if target_box == ' ' else '*'
                    self.current_maze[new_row][new_col] = '@'  # Move player to box's position
                    self.current_maze[row][col] = ' ' if current == '@' else '.'  # Update previous position
                    return

        # Move player only (lowercase moves)
        if target in [' ', '.']:  # Free space or switch
            self.current_maze[new_row][new_col] = '@'  # Move player to target
            self.current_maze[row][col] = ' ' if current == '@' else '.'  # Update previous position

def main():
    root = tk.Tk()
    app = SokobanGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
