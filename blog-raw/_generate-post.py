import re
from datetime import datetime
import os
import sys
import time
import frontmatter
import markdown

OUTPUT_DIRECTORY = r"..\blog"
HTML_TEMPLATE = "z-html-template.html"
BLOG_FILE = r"C:\FILESC\cs\my-site\blog.html"

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text) 
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')

def readable_from_unixtime(timestamp):
    dt_object = datetime.fromtimestamp(timestamp)
    return dt_object.strftime("%b %d %y").lower()

def update_blog_index(metadata):
    """Adds a new post entry to the blog index (blog.html)."""
    try:
        if not os.path.exists(BLOG_FILE):
            print(f"Error: Blog index file '{BLOG_FILE}' not found. Skipping update.")
            return

        # 1. Read the existing blog.html content
        with open(BLOG_FILE, 'r', encoding='utf-8') as f:
            blog_content = f.read()

        # 2. Prepare the new list item
        readable_date = readable_from_unixtime(metadata['published'])
        html_filename = slugify(metadata['title']) + '.html'
        
        # FIX: Explicitly use forward slash (/) for the HTML link path
        # os.path.basename(OUTPUT_DIRECTORY).strip('.\\/') evaluates to 'blog'
        blog_dir_name = os.path.basename(OUTPUT_DIRECTORY).strip('.\\/')
        link_path = f"{blog_dir_name}/{html_filename}"

        new_entry = f'\t<li>{readable_date} - <a href="{link_path}">{metadata["title"]}</a></li>'
        
        # 3. Find the insertion point and insert the new entry
        insertion_tag = '<ol reversed id="posts">'
        
        if insertion_tag in blog_content:
            new_blog_content = blog_content.replace(
                insertion_tag, 
                f'{insertion_tag}\n{new_entry}'
            )

            # 4. Write the updated content back to blog.html
            with open(BLOG_FILE, 'w', encoding='utf-8') as f:
                f.write(new_blog_content)
            
            print(f"Successfully added new entry to {os.path.basename(BLOG_FILE)}.")
        else:
            print(f"Error: Could not find '{insertion_tag}' in {os.path.basename(BLOG_FILE)}. Skipping update.")

    except Exception as e:
        print(f"An error occurred while updating the blog index: {e}")

def generate_html(metadata, content):
    if not os.path.exists(HTML_TEMPLATE):
        print(f"Error: HTML template file '{HTML_TEMPLATE}' not found.")
        return
    
    try:
        with open(HTML_TEMPLATE, 'r', encoding='utf-8') as f:
            template_content = f.read()

        output_html = template_content.replace("!TITLE", metadata['title'])

        html_content = markdown.markdown(content)
        output_html = output_html.replace("!BODY", html_content)

        published_date = readable_from_unixtime(metadata['published'])
        output_html = output_html.replace("!PUBLISH_READABLE", published_date)

        if metadata.get('edited') is not None:
            edit_date = readable_from_unixtime(metadata['edited'])
        
            if edit_date != published_date:
                output_html = output_html.replace("", "edited " + edit_date)

        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

        output_filename = slugify(metadata['title']) + '.html'
        output_filepath = os.path.join(OUTPUT_DIRECTORY, output_filename)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(output_html)

        print(f"Successfully generated HTML file at: {output_filepath}")

        user_input = input("Open in browser? (y/n): ")
        if user_input == "y":
            try:
                os.system(f'start msedge "{os.path.abspath(output_filepath)}"')
                print(f"Opening {output_filename} in your default browser...")
            except Exception as e:
                print(f"Could not open browser: {e}")

    except Exception as e:
        print(f"An error occurred while generating HTML: {e}")

def main():
    while True:
        try:
            print(); # empty line
            user_input = input("Enter a .md filepath (or return to quit): ")
            filepath = user_input.strip('"\'')

            if filepath == "":
                sys.exit(0)

            if not os.path.exists(filepath): 
                print("Error: filepath \"" + filepath + "\" could not be found.")
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                md_text = f.read()

            try:
                post = frontmatter.loads(md_text)
                metadata = post.metadata
                content = post.content

                user_input = input("[p]ublish or [u]pdate file?: ")
                command = user_input.lower()
                timestamp = int(time.time())
                
                is_publish_command = False
                
                print()
                if command == 'p':
                    metadata['published'] = timestamp
                    print(f"Setting publish date to: {metadata['published']}")
                    is_publish_command = True
                elif command == 'u':
                    if 'published' in metadata:
                         metadata['edited'] = timestamp
                         print(f"Setting update date to: {metadata['edited']}")
                    else:
                        print("Cannot 'u'pdate a file without a 'published' date. Use 'p' to publish.")
                        continue
                else:
                    print("Invalid command. No timestamp was set.")
                    continue

                # Renaming and Saving
                new_filepath = slugify(metadata['title']) + '.md'
                if not os.path.exists(new_filepath) or new_filepath != filepath:
                    try:
                        os.rename(filepath, new_filepath)
                        print(f"File renamed to: {new_filepath}")
                    except FileNotFoundError:
                        # If the file was not renamed because it already existed with the new name
                        # and the initial path was a relative/simple name, we just proceed.
                        pass
                
                with open(new_filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                print(f"Saved updated metadata to {new_filepath}")
                
                # 1. Generate the HTML blog post
                generate_html(metadata, content)

                # 2. Update the blog index file *only* if publishing a new post
                if is_publish_command:
                    update_blog_index(metadata)

            except Exception as e:
                print(f"Error processing file: {e}")
        
        except KeyboardInterrupt:
            print("\nExiting program.")
            sys.exit(0)

if __name__ == "__main__":
    main()
