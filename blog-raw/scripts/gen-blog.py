import os
import re
from datetime import datetime

def extract_blog_info(html_content):
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
    blog_entries = []

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                blog_info = extract_blog_info(content)

                if blog_info["title"] and blog_info["date_created"]:
                    blog_info["filename"] = filename
                    blog_entries.append(blog_info)

    return blog_entries

def format_blog_entries_as_cards(blog_entries):
    def parse_date(date_str):
        return datetime.strptime(date_str, '%b %d %y %I:%M%p')

    sorted_entries = sorted(blog_entries, key=lambda x: parse_date(x["date_created"]), reverse=True)

    card_elements = []
    for entry in sorted_entries:
        if entry['tags'].lower() == "none":
            tag_text = ""
        else:
            tag_list_raw = [tag.strip() for tag in entry['tags'].split(',') if tag.strip()]
            if 'short' in tag_list_raw:
                tag_list_raw = ['short'] + [tag for tag in tag_list_raw if tag != 'short']

            tag_list = []
            for tag in tag_list_raw:
                if tag == "short":
                    tag_list.append(f'<span class="tag-label minipost">{tag}</span>')
                else:
                    tag_list.append(f'<span class="tag-label">{tag}</span>')
            tag_text = ", ".join(tag_list)

        card_html = f'''
        <div class="card">
            <a href="blog/{entry["filename"]}">{entry["title"]}</a>
            <p>{entry["date_created"][:9]}, {entry["word_count"]} words<br>{tag_text}</p>
        </div>'''.strip()

        card_elements.append(card_html)

    return "\n".join(card_elements)

def update_blog_page(blog_page_path, blog_entries):
    card_formatted = format_blog_entries_as_cards(blog_entries)

    with open(blog_page_path, 'r+', encoding='utf-8') as file:
        content = file.read()

        match = re.search(
            r'(<div[^>]*\bid="container"[^>]*>)(.*?)(</div>)',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        if not match:
            raise ValueError("Could not find container div")

        new_container = f"{match.group(1)}\n{card_formatted}\n{match.group(3)}"
        new_content = content[:match.start()] + new_container + content[match.end():]

        with open(blog_page_path, 'w', encoding='utf-8') as file:
            file.write(new_content)


    print(f"Updated {blog_page_path} with fully rebuilt container.")

def update_post_html_titles(directory, blog_entries):
    for entry in blog_entries:
        filepath = os.path.join(directory, entry["filename"])
        with open(filepath, 'r+', encoding='utf-8') as file:
            content = file.read()
            new_title_tag = f"<title>{entry['title']}</title>"
            if "<title>" in content:
                content = re.sub(r"<title>.*?</title>", new_title_tag, content, flags=re.IGNORECASE)
            else:
                content = re.sub(r"(<head[^>]*>)", r"\1\n" + new_title_tag, content, flags=re.IGNORECASE)
            file.seek(0)
            file.write(content)
            file.truncate()
    print("Updated <title> tags in individual blog post HTML files.")

# Example usage
blog_directory = "C:\\FILESC\\cs\\mysite\\blog"
blog_page_path = "C:\\FILESC\\cs\\mysite\\blog.html"

blog_entries = extract_all_blog_info(blog_directory)
update_post_html_titles(blog_directory, blog_entries)
update_blog_page(blog_page_path, blog_entries)
