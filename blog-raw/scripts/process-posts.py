import os
import time
import shutil
import glob
import re

class Post:
    def __init__(self, publish_date, update_date, title, body, word_count, hyphenated_title):
        self.publish_date = publish_date
        self.update_date = update_date
        self.title = title
        self.body = body
        self.word_count = word_count
        self.hyphenated_title = hyphenated_title
        
def get_time():
    return int(time.time());

def set_date(is_pub, filepath):
    if is_pub:
        date_type = "publish-date"
    else:
        date_type = "update-date"

    with open(filepath, 'r+') as file:
        content = file.read()
        content = re.sub(rf'{date_type}:.*?;', f'{date_type}: {get_time()};', content)
        file.seek(0)
        file.write(content)
        file.truncate()
        print(f"set {date_type} to {filepath}")

def get_yes_no(question):
    response = input(question)
    if response == "y" or response == "Y":
        return True
    elif response == "n" or response == "N":
        return False
    else:
        print("could not parse answer.")
        return get_yes_no(question)

def start():
    command = input("type 'publish <filename.txt>' or 'update <filename.txt>' to continue: ")
    command_parts = command.split()

    if len(command_parts) == 2 and command_parts[0] in ["publish", "update"]:
        filename = command_parts[1]
        directory = "C:\\FILESC\\cs\\mysite\\blog-raw"  
        files_found = glob.glob(os.path.join(directory, filename))

        if command_parts[0] == "publish":
            is_pub = True
        else:
            is_pub = False
    
        if files_found:
            print(f"Found file: {files_found[0]}")
            my_post = parse_file(files_found[0])
        else:
            print(f"File '{filename}' not found in the directory.")
    else:
        print("Invalid command format")
        
    #print(f"word count: {my_post.word_count}")

    if my_post.publish_date != "null" and is_pub:
        answer = get_yes_no("Post already contains a published date. Overwrite? (y/n)")
        if answer:
            set_date(True, files_found[0])
            my_post.publish_date = get_time()
    elif my_post.publish_date == "null" and is_pub:
        set_date(True, files_found[0])
        my_post.publish_date = get_time()

    if not is_pub:
        set_date(False, files_found[0])
        my_post.update_date = get_time()

    #os.rename(files_found[0], f'{my_post.hyphenated_title}.txt') just annoying having the longer name
    insert_into_template(my_post, is_pub)

def insert_into_template(my_post, is_pub):
    template_path = "C:\\FILESC\\cs\\mysite\\blog-raw\\template.html"

    with open(template_path, 'r', encoding='utf-8') as file:
        tc = file.read()

    tc = tc.replace('blog</a> / ', f'blog</a> / {my_post.title}')
    tc = tc.replace('</p>', f'{my_post.body}</p>')
    tc = tc.replace('<word count:>', f'<word count:{my_post.word_count}>')

    tc = tc.replace('date-created"></span>', f'date-created">{timestamp_to_readable(my_post.publish_date)}</span>')
    
    if my_post.update_date != "null":
        tc = tc.replace('<i id="last-modified"></i>', f'<br /><i id="last-modified">last modified {timestamp_to_readable(my_post.update_date)}</i>')

    output_path = f"C:\\FILESC\\cs\\mysite\\blog\\{my_post.hyphenated_title}.html"

    with open(output_path, 'w', encoding='utf-8') as output_file:
        output_file.write(tc)

    if is_pub:
        print(f"Published to {output_path}")
    else:
        print(f"Updated {output_path}")

def timestamp_to_readable(timestamp):
    try:
        timestamp = int(timestamp)
        return time.strftime('%b %d %y %I:%M%p', time.localtime(timestamp)).lower()

    except (ValueError, TypeError):
        raise ValueError("Timestamp must be convertible to an integer")

def extract(content, start_flag):
    start_index_title = content.find(start_flag)
    if start_index_title != -1:
        end_index_title = content.find(";", start_index_title)
        if end_index_title != -1:
            title = content[start_index_title + len(start_flag):end_index_title].strip()
            print(f"Parsed {start_flag} {title}")
            return title
        else:
            print("No terminating ';' found for the title.")
    else:
        print(f"No {start_flag} found in the file..")

def parse_file(filepath):
    try:
        with open(filepath, 'r') as file:
            content = file.read()

            title = extract(content, "title:")
            publish_date = extract(content, "publish-date:")
            update_date = extract(content, "update-date:")

            body_start = content.find("<body>")
            if body_start != -1:
                body_content = content[body_start + len("<body>"):] .strip()
                #print(f"Body content:\n{body_content}")
            else:
                print("No <body> tag found in the file.")

            hyphenated_title = title.replace(' ', '-')
            hyphenated_title = hyphenated_title.lower()
            return Post(publish_date, update_date, title, body_content, len(body_content.split()), hyphenated_title)

    except Exception as e:
        print(f"Error reading the file: {e}")

start()
