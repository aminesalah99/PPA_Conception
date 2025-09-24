import os

def generate_tree(path, prefix="", max_depth=None, current_depth=0):
    """
    Generate a directory tree structure.
    
    Args:
        path: The directory path to scan
        prefix: Prefix for each line (used for recursion)
        max_depth: Maximum depth to traverse (None for no limit)
        current_depth: Current depth in recursion
        
    Returns:
        String representation of the directory tree
    """
    if max_depth is not None and current_depth > max_depth:
        return ""
    
    items = os.listdir(path)
    # Sort directories first, then files
    items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
    
    tree = ""
    pointers = ["├── "] * (len(items) - 1) + ["└── "]
    
    for i, item in enumerate(items):
        item_path = os.path.join(path, item)
        
        # Skip hidden files and directories (optional)
        if item.startswith('.'):
            continue
            
        tree += prefix + pointers[i] + item + "\n"
        
        if os.path.isdir(item_path) and (max_depth is None or current_depth < max_depth):
            extension = "│   " if i < len(items) - 1 else "    "
            tree += generate_tree(item_path, prefix + extension, max_depth, current_depth + 1)
    
    return tree

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generate the tree structure
    tree_structure = generate_tree(script_dir)
    
    # Create the output file
    output_file = os.path.join(script_dir, "directory_tree.txt")
    
    # Write the tree to the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Directory Tree for: {script_dir}\n")
        f.write("=" * 50 + "\n\n")
        f.write(tree_structure)
    
    print(f"Directory tree has been saved to: {output_file}")

if __name__ == "__main__":
    main()
