import os
import time
import glob
import re
import sys

class Post:
    def __init__(self, publish_date, update_date, title, body, word_count, hyphenated_title):
        self.publish_date = publish_date
        self.update_date = update_date
        self.title = title
        self.body = body
        self.word_count = word_count
        self.hyphenated_title = hyphenated_title

def get_time():
    return int(time.time())

def set_date(is_pub, filepath):
    date_type = "publish-date" if is_pub else "update-date"
    with open(filepath, 'r+', encoding='utf-8') as file:
        content = file.read()
        content = re.sub(rf'{date_type}:.*?;', f'{date_type}: {get_time()};', content)
        file.seek(0)
        file.write(content)
        file.truncate()
    print(f"Set {date_type} for {filepath}")

def get_yes_no(question):
    while True:
        response = input(f"{question} (y/n): ").strip().lower()
        if response in ["y", "n"]:
            return response == "y"
        print("Invalid response. Please enter 'y' or 'n'.")

def start():
    if len(sys.argv) == 3:
        command_parts = sys.argv[1:]
    else:
        command_parts = input("Type 'publish <filename.txt>' or 'update <filename.txt>' to continue: ").strip().split()

    if len(command_parts) != 2 or command_parts[0] not in ["publish", "update"]:
        print("Invalid command format")
        return

    filename, is_pub = command_parts[1], command_parts[0] == "publish"
    directory = "C:\\FILESC\\cs\\mysite\\blog-raw"
    files_found = glob.glob(os.path.join(directory, filename))

    if not files_found:
        print(f"File '{filename}' not found.")
        return

    file_path = files_found[0]
    print(f"Found file: {file_path}")
    my_post = parse_file(file_path)

    if is_pub and my_post.publish_date != "null":
        if not get_yes_no("Post already contains a published date. Overwrite?"):
            return

    set_date(is_pub, file_path)
    if is_pub:
        my_post.publish_date = get_time()
    else:
        my_post.update_date = get_time()

    insert_into_template(my_post, is_pub)
    os.system("python gen-blog.py")

def insert_into_template(my_post, is_pub):
    template_path = "C:\\FILESC\\cs\\mysite\\blog-raw\\scripts\\template.html"
    output_path = f"C:\\FILESC\\cs\\mysite\\blog\\{my_post.hyphenated_title}.html"

    with open(template_path, 'r', encoding='utf-8') as file:
        template_content = file.read()

    replacements = {
        'blog</a> / ': f'blog</a> / {my_post.title}',
        '</p>': f'{my_post.body}</p>',
        '<word count:>': f'<word count:{my_post.word_count}>',
        'date-created"></span>': f'date-created">{timestamp_to_readable(my_post.publish_date)}</span>'
    }

    if my_post.update_date != "null":
        replacements['<i id="last-modified"></i>'] = f'<br /><i id="last-modified">last modified {timestamp_to_readable(my_post.update_date)}</i>'

    for key, value in replacements.items():
        template_content = template_content.replace(key, value)

    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(template_content)

    print(f"{'Published' if is_pub else 'Updated'} to {output_path}")

def timestamp_to_readable(timestamp):
    try:
        return time.strftime('%b %d %y %I:%M%p', time.localtime(int(timestamp))).lower()
    except (ValueError, TypeError):
        raise ValueError("Timestamp must be an integer")

def extract(content, start_flag):
    match = re.search(rf'{start_flag}(.*?);', content)
    if match:
        return match.group(1).strip()
    return "null"

def parse_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()

    title = extract(content, "title:")
    publish_date = extract(content, "publish-date:")
    update_date = extract(content, "update-date:")

    body_match = re.search(r'<body>(.*)', content, re.DOTALL)
    body_content = body_match.group(1).strip() if body_match else ""
    body_content = re.sub(r'##(.+)', r'<strong>\1</strong>', body_content)

    hyphenated_title = title.replace(' ', '-').lower()
    word_count = len(body_content.split())

    return Post(publish_date, update_date, title, body_content, word_count, hyphenated_title)

start()
