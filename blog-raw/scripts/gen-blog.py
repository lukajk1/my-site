import os
import re
from datetime import datetime

def extract_blog_info(html_content):
    """Extracts word count, date, and title from a blog HTML file."""
    word_count_match = re.search(r"<!-- <word count:(\d+)> -->", html_content)
    word_count = int(word_count_match.group(1)) if word_count_match else None

    date_match = re.search(r'id="date-created">(.*?)<', html_content)
    date_created = date_match.group(1) if date_match else None

    title_match = re.search(r'<a href="\.\./blog\.html">blog<\/a> / (.*?)<\/h2>', html_content)
    title = title_match.group(1) if title_match else None

    return {
        "word_count": word_count,
        "date_created": date_created,
        "title": title
    }

def extract_all_blog_info(directory):
    """Extracts blog info from all .html files in the specified directory."""
    blog_entries = []

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                content = file.read()
                blog_info = extract_blog_info(content)
                
                # Ensure valid data before appending
                if blog_info["title"] and blog_info["date_created"]:
                    blog_info["filename"] = filename
                    blog_entries.append(blog_info)

    return blog_entries

def format_blog_entries_as_li(blog_entries):
    """Formats extracted blog entries into sorted <li> elements."""
    
    def parse_date(date_str):
        """Parses the date for sorting purposes."""
        return datetime.strptime(date_str, '%b %d %y %I:%M%p')

    # Sort by date (most recent first)
    sorted_entries = sorted(blog_entries, key=lambda x: parse_date(x["date_created"]), reverse=True)

    li_elements = []
    for entry in sorted_entries:
        li_elements.append(f'''
        <li><a href="blog/{entry["filename"]}">{entry["title"]}</a><br />
        {entry["word_count"]} words<br />
        {entry["date_created"]}</li>
        '''.strip())

    return "<ol reversed>\n" + "\n".join(li_elements) + "\n</ol>"

def update_blog_page(blog_page_path, blog_entries):
    """Updates the blog.html file with the formatted blog list."""
    li_formatted = format_blog_entries_as_li(blog_entries)

    with open(blog_page_path, 'r+') as file:
        content = file.read()
        # Replace the old <ol> block
        content = re.sub(r'<ol reversed>.*?</ol>', li_formatted, content, flags=re.DOTALL)
        file.seek(0)
        file.write(content)
        file.truncate()

    print(f"Updated {blog_page_path} with sorted blog entries.")

blog_directory = "C:\\FILESC\\cs\\mysite\\blog"
blog_page_path = "C:\\FILESC\\cs\\mysite\\blog.html"

blog_entries = extract_all_blog_info(blog_directory)
update_blog_page(blog_page_path, blog_entries)
