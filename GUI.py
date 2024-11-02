import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk  # For handling images
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
        self.solution_path = ""
        self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
        self.output_dir = output_dir
        self.tile_images = {}  # To store tile images

        # Load tileset images
        self.load_tileset()

        # Setup GUI components
        self.setup_gui()
        
    def load_tileset(self):
        # Load each tile image and resize to fit cell size
        self.tile_images = {
            '#': ImageTk.PhotoImage(Image.open("tileset/wall.png")),
            ' ': ImageTk.PhotoImage(Image.open("tileset/free_space.png")),
            '@': ImageTk.PhotoImage(Image.open("tileset/ares.png")),
            '$': ImageTk.PhotoImage(Image.open("tileset/stone.png")),
            '.': ImageTk.PhotoImage(Image.open("tileset/switch.png")),
            '*': ImageTk.PhotoImage(Image.open("tileset/stone_on_switch.png")),
            '+': ImageTk.PhotoImage(Image.open("tileset/ares_on_switch.png"))
        }
    
    def setup_gui(self):
        # Top control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Algorithm selection
        ttk.Label(control_frame, text="Algorithm:").grid(row=0, column=0, padx=5)
        self.algo_var = tk.StringVar(value="UCS")
        algo_combo = ttk.Combobox(control_frame, textvariable=self.algo_var, 
                                  values=["UCS", "BFS", "DFS", "A*"], state="readonly")
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
        
        # Maze canvas
        self.canvas_frame = ttk.Frame(self.root, padding="10")
        self.canvas_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.canvas = tk.Canvas(self.canvas_frame, width=500, height=500)
        self.canvas.grid(row=0, column=0)
        
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
        output_file = os.path.join(self.output_dir, f"output-{test_case}.txt")

        if not os.path.exists(output_file):
            print("Output file not found.")
            return
        
        # Read output file
        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Find the relevant algorithm section
        algo_index = next((i for i, line in enumerate(lines) if line.startswith(algo)), None)
        if algo_index is None:
            print("Algorithm result not found in the output file.")
            return

        # Parse solution details or "No solution"
        if "No solution" in lines[algo_index + 1]:
            self.solution_path = ""
            self.stats = {"steps": 0, "weight": 0, "nodes": 0, "time": 0, "memory": 0}
            print("No solution found for the selected algorithm.")
            self.update_stats(no_solution=True)
        else:
            # Extract stats and solution path
            stats_line = lines[algo_index + 1]
            self.solution_path = lines[algo_index + 2].strip()

            # Parse statistics
            self.stats["steps"] = int(stats_line.split("Steps:")[1].split(",")[0].strip())
            self.stats["weight"] = int(stats_line.split("Weight:")[1].split(",")[0].strip())
            self.stats["nodes"] = int(stats_line.split("Nodes:")[1].split(",")[0].strip())
            self.stats["time"] = float(stats_line.split("Time (ms):")[1].split(",")[0].strip())
            self.stats["memory"] = float(stats_line.split("Memory (MB):")[1].strip())

            # Reset maze and update initial display
            self.current_step = 0
            self.reset_maze()
            self.update_display()
            self.update_stats()
    
    def update_display(self):
        self.canvas.delete("all")
        if not self.current_maze:
            return

        canvas_width = 500
        canvas_height = 500
        cell_size = min(canvas_width // len(self.current_maze[0]),
                        canvas_height // len(self.current_maze))
        
        for i, row in enumerate(self.current_maze):
            for j, cell in enumerate(row):
                x1 = j * cell_size
                y1 = i * cell_size
                self.canvas.create_image(x1, y1, anchor="nw", image=self.tile_images[cell])

    def update_stats(self, no_solution=False):
        if no_solution:
            self.stats_labels["Steps"].config(text="No solution")
            self.stats_labels["Weight"].config(text="N/A")
            self.stats_labels["Nodes"].config(text="N/A")
            self.stats_labels["Time (ms)"].config(text="N/A")
            self.stats_labels["Memory (MB)"].config(text="N/A")
        else:
            self.stats_labels["Steps"].config(text=f"{self.current_step}/{self.stats['steps']}")
            self.stats_labels["Weight"].config(text=f"{self.stats['weight']}")
            self.stats_labels["Nodes"].config(text=f"{self.stats['nodes']}")
            self.stats_labels["Time (ms)"].config(text=f"{self.stats['time']:.2f}")
            self.stats_labels["Memory (MB)"].config(text=f"{self.stats['memory']:.2f}")
    
    def step_forward(self):
        if self.current_step < len(self.solution_path):
            move = self.solution_path[self.current_step]
            self.current_maze = self.apply_move(self.current_maze, move)
            self.current_step += 1
            self.update_display()
            self.update_stats()
    
    def step_backward(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.reset_maze()
            for i in range(self.current_step):
                move = self.solution_path[i]
                self.current_maze = self.apply_move(self.current_maze, move)
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
        # Reset maze to initial state if needed
        pass

    def apply_move(self, maze, move):
        new_maze = copy.deepcopy(maze)
        # Logic for updating maze based on move
        return new_maze

def main():
    root = tk.Tk()
    app = SokobanGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
