import os
import uuid
import re
import sys
import subprocess # Added for clipboard operations

# Configuration
HASH_LENGTH = 8
HASH_PATTERN = re.compile(f'^[0-9a-fA-F]{{{HASH_LENGTH}}}$')

# List of common image file extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']

def copy_to_clipboard(text):
    """Copies text to the system clipboard using subprocess for cross-platform support."""
    try:
        if os.name == 'nt':  # Windows
            # Use 'clip' command
            subprocess.run(['clip'], input=text.encode('utf-8'), check=True, shell=True)
            return True
        elif sys.platform == 'darwin':  # macOS
            # Use 'pbcopy' command
            subprocess.run(['pbcopy'], input=text.encode('utf-8'), check=True)
            return True
        else: # Linux/Other (assumes xclip)
            # Requires 'xclip' or 'xsel' to be installed
            subprocess.run(['xclip', '-selection', 'clipboard'], input=text.encode('utf-8'), check=True)
            return True
    except FileNotFoundError:
        print("\n[CLIPBOARD ERROR] System clipboard utility not found (requires 'clip', 'pbcopy', or 'xclip').")
        print("Please ensure the appropriate utility is installed and accessible.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n[CLIPBOARD ERROR] Failed to copy to clipboard: {e}")
        return False
    except Exception as e:
        print(f"\n[CLIPBOARD ERROR] An unexpected error occurred: {e}")
        return False

def generate_hex_hash():
    """Generates a random 8-character hexadecimal string."""
    # Using uuid4 and slicing provides a good source of randomness
    return uuid.uuid4().hex[:HASH_LENGTH]

def generate_unique_folder():
    """Generates a new folder in the current directory with a unique hash name."""
    print("Generating new hashed folder...")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Loop until a unique folder name is found
    while True:
        folder_name = generate_hex_hash()
        new_path = os.path.join(current_dir, folder_name)

        if not os.path.exists(new_path):
            try:
                os.makedirs(new_path)
                print(f"Successfully created new folder: {new_path}")
                return
            except OSError as e:
                print(f"Error creating directory {new_path}: {e}")
                return
        # If folder exists, loop and generate a new hash

def is_hash_name(filename_without_ext):
    """Checks if the filename (without extension) matches the hash pattern."""
    return HASH_PATTERN.match(filename_without_ext) is not None

def process_existing_folder(folder_path):
    """
    Checks if a folder exists and then ensures all files within it are 
    named with a unique hash. Renames files if necessary.
    """
    print(f"Processing folder: {folder_path}")

    if not os.path.isdir(folder_path):
        print(f"Error: Path does not exist or is not a directory: {folder_path}")
        return

    # Keep track of generated hashes to prevent collisions within this session
    used_hashes = set()
    
    # 1. First Pass: Collect existing hashes and identify files needing rename
    files_to_rename = []
    
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        
        # Skip directories
        if os.path.isdir(filepath):
            continue

        name, ext = os.path.splitext(filename)
        
        if is_hash_name(name):
            used_hashes.add(name.lower())
        else:
            files_to_rename.append((filepath, ext))

    # 2. Second Pass: Rename files that need a unique hash
    if not files_to_rename:
        print("All files already conform to the hash naming convention. Nothing to do.")
        return

    print(f"\nFound {len(files_to_rename)} file(s) requiring rename...")
    
    for old_filepath, ext in files_to_rename:
        old_filename = os.path.basename(old_filepath)
        
        # Generate a new unique hash
        new_hash = generate_hex_hash()
        while new_hash in used_hashes:
            new_hash = generate_hex_hash()
        
        used_hashes.add(new_hash)
        
        new_filename = new_hash + ext
        new_filepath = os.path.join(folder_path, new_filename)

        try:
            os.rename(old_filepath, new_filepath)
            print(f"  Renamed '{old_filename}' to '{new_filename}'")
        except OSError as e:
            print(f"  Error renaming {old_filename}: {e}")

    print("\nFolder processing complete.")


def main():
    while True:
        try:
            print("\n--- File Management Utility ---")
            
            # Updated prompt text
            user_input = input(
                "Enter: Folder path to process | 'h' to create a new folder | [Image Filepath] to copy formatted Markdown: "
            ).strip().strip('"\'') # Clean up surrounding quotes
            
            # Check for 'h' (hashed folder creation)
            if user_input.lower() == 'h':
                # Option 1: Generate new folder
                generate_unique_folder()
            elif user_input == '':
                # If the user presses Enter without input, prompt them again
                continue
            
            # Check for Option 3: Image File Path (Copy to clipboard)
            elif os.path.isfile(user_input):
                name, ext = os.path.splitext(user_input)
                if ext.lower() in IMAGE_EXTENSIONS:
                    # Construct the Markdown image tag
                    # Placeholder 'alt text here' is used, as the script cannot know the actual alt text
                    markdown_link = f"![alt text here]({user_input})"
                    
                    # Attempt to copy the formatted Markdown link
                    if copy_to_clipboard(markdown_link):
                        print(f"Markdown image link successfully copied to clipboard: {markdown_link}")
                else:
                    print(f"Error: '{user_input}' is a file, but not a recognized image type for copying.")

            else:
                # Option 2: Process existing folder path
                process_existing_folder(user_input)
                
        except KeyboardInterrupt:
            print("\nExiting utility.")
            sys.exit(0)

if __name__ == "__main__":
    main()
