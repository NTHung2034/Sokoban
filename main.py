from Algorithms import bfs, dfs, ucs, a_start
import os
import glob

def clear_output_folder():
    # Get the path to the Outputs folder
    output_path = os.path.join(os.getcwd(), 'Outputs')
    
    # Check if the Outputs folder exists
    if not os.path.exists(output_path):
        print("Creating Outputs folder...")
        os.makedirs(output_path)
        return
    
    # Find and remove all files in the Outputs folder
    files = glob.glob(os.path.join(output_path, '*'))
    for file in files:
        try:
            os.remove(file)
            print(f"Cleared: {os.path.basename(file)}")
        except Exception as e:
            print(f"Error removing {file}: {e}")

def main():
    print("Clearing previous output files...")
    clear_output_folder()
    
    print("\nRunning BFS algorithm...")
    bfs.main()
    
    print("Running DFS algorithm...")
    dfs.main()
    
    print("Running UCS algorithm...")
    ucs.main()
    
    print("Running A* algorithm...")
    a_start.main()
    
    print("\nAll algorithms completed!")

if __name__ == '__main__':
    main()