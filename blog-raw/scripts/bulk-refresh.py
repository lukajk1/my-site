import os
import glob
import subprocess

# Define directory containing .txt blog source files
raw_blog_dir = "C:\\FILESC\\cs\\mysite\\blog-raw"
script_path = os.path.join(raw_blog_dir, "scripts", "process-post.py")

# Find all .txt files
txt_files = glob.glob(os.path.join(raw_blog_dir, "*.txt"))

for filepath in txt_files:
    filename = os.path.basename(filepath)
    print(f"Refreshing {filename}...")
    subprocess.run(["python", script_path, "refresh", filename])
