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

        if metadata['edited'] is not None:
            edit_date = readable_from_unixtime(metadata['edited'])
        
            if edit_date != published_date:
                output_html = output_html.replace("<!-- !EDITED_READABLE -->", edit_date)

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
            filepath = user_input.strip('"\'')  # Just strip quotes directly from the input

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

                print()
                if command == 'p':
                    metadata['published'] = timestamp
                    print(f"Setting publish date to: {metadata['published']}")
                elif command == 'u':
                    metadata['edited'] = timestamp
                    print(f"Setting update date to: {metadata['edited']}")
                else:
                    print("Invalid command. No timestamp was set.")

                new_filepath = slugify(metadata['title']) + '.md'
                os.rename(filepath, new_filepath)

                with open(new_filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                print(f"Saved updated metadata to {new_filepath}")

                generate_html(metadata, content)


            except Exception as e:
                print(f"Error processing file: {e}")
        
        except KeyboardInterrupt:
            print("\nExiting program.")
            sys.exit(0)

if __name__ == "__main__":
    main()