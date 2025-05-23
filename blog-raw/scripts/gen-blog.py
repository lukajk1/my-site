import os
import re
from datetime import datetime

def extract_blog_info(html_content):
    """Extracts word count, date, title, and tags from a blog HTML file."""
    word_count_match = re.search(r"<!-- <word count:(\d+)>", html_content)
    word_count = int(word_count_match.group(1)) if word_count_match else None

    date_match = re.search(r'id="date-created">(.*?)<', html_content)
    date_created = date_match.group(1) if date_match else None

    title_match = re.search(r'<a href="\.\./blog\.html">blog<\/a> / (.*?)<\/h2>', html_content)
    title = title_match.group(1) if title_match else None

    tags_match = re.search(r'<!-- <word count:\d+> <tags:(.*?)>-->', html_content)
    tags = tags_match.group(1).strip() if tags_match else "none"

    return {
        "word_count": word_count,
        "date_created": date_created,
        "title": title,
        "tags": tags
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

                if blog_info["title"] and blog_info["date_created"]:
                    blog_info["filename"] = filename
                    blog_entries.append(blog_info)

    return blog_entries

def format_blog_entries_as_li(blog_entries):
    """Formats extracted blog entries into sorted <li> elements."""

    def parse_date(date_str):
        return datetime.strptime(date_str, '%b %d %y %I:%M%p')

    sorted_entries = sorted(blog_entries, key=lambda x: parse_date(x["date_created"]), reverse=True)

    li_elements = []
    for entry in sorted_entries:
        if entry['tags'].lower() == "none":
            tag_text = " - tags: none"
        else:
            tag_list = [f'<span class="tag-label">{tag.strip()}</span>' for tag in entry['tags'].split(',') if tag.strip()]
            tag_text = " - tags: " + ", ".join(tag_list)

        li_elements.append(f'''
        <li><a href="blog/{entry["filename"]}">{entry["title"]}</a><br />
        {entry["word_count"]} words - {entry["date_created"][:9]}{tag_text}</li>
        '''.strip())

    return "<ol reversed>\n" + "\n".join(li_elements) + "\n</ol>"

def update_blog_page(blog_page_path, blog_entries):
    """Updates the blog.html file with the formatted blog list."""
    li_formatted = format_blog_entries_as_li(blog_entries)

    with open(blog_page_path, 'r+') as file:
        content = file.read()
        content = re.sub(r'<ol reversed>.*?</ol>', li_formatted, content, flags=re.DOTALL)
        file.seek(0)
        file.write(content)
        file.truncate()

    print(f"Updated {blog_page_path} with sorted blog entries.")

def update_post_html_titles(directory, blog_entries):
    """Updates the <title> tag in each blog HTML file to include the post title."""
    for entry in blog_entries:
        filepath = os.path.join(directory, entry["filename"])
        with open(filepath, 'r+', encoding='utf-8') as file:
            content = file.read()

            # Replace or insert the <title> tag
            new_title_tag = f"<title>{entry['title']}</title>"
            if "<title>" in content:
                content = re.sub(r"<title>.*?</title>", new_title_tag, content, flags=re.IGNORECASE)
            else:
                # Insert <title> right after <head> if <title> tag does not exist
                content = re.sub(r"(<head[^>]*>)", r"\1\n" + new_title_tag, content, flags=re.IGNORECASE)

            file.seek(0)
            file.write(content)
            file.truncate()

    print("Updated <title> tags in individual blog post HTML files.")



blog_directory = "C:\\FILESC\\cs\\mysite\\blog"
blog_page_path = "C:\\FILESC\\cs\\mysite\\blog.html"

blog_entries = extract_all_blog_info(blog_directory)
update_post_html_titles(blog_directory, blog_entries)
update_blog_page(blog_page_path, blog_entries)

