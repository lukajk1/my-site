#!/usr/bin/env python3
"""
Blog post processing script for converting raw text files to HTML.
Handles publishing, updating, and refreshing blog posts.
"""

import os
import time
import glob
import re
import sys
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class PostAction(Enum):
    """Enum for different post actions."""
    PUBLISH = "publish"
    UPDATE = "update"  
    REFRESH = "refresh"


@dataclass
class BlogPost:
    """Data class representing a blog post."""
    title: str
    body: str
    word_count: int
    hyphenated_title: str
    tags: str
    publish_date: Optional[int] = None
    update_date: Optional[int] = None

    @property
    def is_published(self) -> bool:
        """Check if post has been published."""
        return self.publish_date is not None and str(self.publish_date) != "null"

    @property
    def is_short_post(self) -> bool:
        """Check if post qualifies as a short post."""
        return self.word_count <= 200


class BlogPostProcessor:
    """Main class for processing blog posts."""
    
    def __init__(self, blog_raw_dir: str = "C:\\FILESC\\cs\\mysite\\blog-raw"):
        self.blog_raw_dir = Path(blog_raw_dir)
        self.template_path = self.blog_raw_dir / "scripts" / "template.html"
        self.blog_output_dir = Path("C:\\FILESC\\cs\\mysite\\blog")
        self.gen_blog_script = Path("gen-blog.py")

    def get_current_timestamp(self) -> int:
        """Get current Unix timestamp."""
        return int(time.time())

    def timestamp_to_readable(self, timestamp: Optional[int]) -> str:
        """Convert Unix timestamp to readable format."""
        if timestamp is None or str(timestamp) == "null":
            raise ValueError("Invalid timestamp")
        
        try:
            return time.strftime('%b %d %y %I:%M%p', time.localtime(timestamp)).lower()
        except (ValueError, TypeError, OSError):
            raise ValueError("Timestamp must be a valid integer")

    def get_user_confirmation(self, question: str) -> bool:
        """Get yes/no confirmation from user."""
        while True:
            try:
                response = input(f"{question} (y/n): ").strip().lower()
                if response in ["y", "yes"]:
                    return True
                elif response in ["n", "no"]:
                    return False
                print("Invalid response. Please enter 'y' or 'n'.")
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user")
                return False

    def extract_field(self, content: str, field_name: str) -> str:
        """Extract a field value from post content."""
        pattern = rf'{re.escape(field_name)}:\s*(.*?);'
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else "null"

    def update_field_in_file(self, filepath: Path, field_name: str, value: int) -> None:
        """Update a field value in the source file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            escaped_field = re.escape(field_name)
            pattern = rf'{escaped_field}:\s*.*?;'
            replacement = f'{field_name}: {value};'
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"Updated {field_name} in {filepath.name}")
        except IOError as e:
            raise RuntimeError(f"Failed to update {field_name} in {filepath}: {e}")

    def parse_post_file(self, filepath: Path) -> BlogPost:
        """Parse a blog post file and return a BlogPost object."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read file {filepath}: {e}")

        # Extract metadata
        title = self.extract_field(content, "title")
        if title == "null":
            raise ValueError(f"No title found in {filepath}")
            
        publish_date_str = self.extract_field(content, "publish-date")
        update_date_str = self.extract_field(content, "update-date")
        tags = self.extract_field(content, "tags")

        # Parse timestamps with error handling
        try:
            publish_date = None if publish_date_str == "null" else int(publish_date_str)
            update_date = None if update_date_str == "null" else int(update_date_str)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format in {filepath}: {e}")

        # Extract body content
        body_match = re.search(r'<body>(.*)', content, re.DOTALL)
        if not body_match:
            raise ValueError(f"No <body> section found in {filepath}")
        
        body_content = body_match.group(1).strip()
        
        # Process markdown-style formatting
        body_content = re.sub(r'##(.+)', r'<strong>\1</strong>', body_content)

        # Generate hyphenated title for filename with better sanitization
        hyphenated_title = re.sub(r'[^\w\s-]', '', title).strip()
        hyphenated_title = re.sub(r'[-\s]+', '-', hyphenated_title).lower()
        
        if not hyphenated_title:
            raise ValueError(f"Could not generate valid filename from title: {title}")
        
        # Calculate word count from plain text (strip HTML tags)
        plain_text = re.sub(r'<[^>]+>', ' ', body_content)
        word_count = len([word for word in plain_text.split() if word.strip()])

        # Process tags
        processed_tags = self._process_tags(tags, word_count)

        return BlogPost(
            title=title,
            body=body_content,
            word_count=word_count,
            hyphenated_title=hyphenated_title,
            tags=processed_tags,
            publish_date=publish_date,
            update_date=update_date
        )

    def _process_tags(self, tags: str, word_count: int) -> str:
        """Process and sort tags, adding 'short' tag if applicable."""
        if not tags or tags.lower() == "null":
            tag_list = []
        else:
            tag_list = [tag.strip().lower() for tag in tags.split(',') if tag.strip()]
            # Remove duplicates while preserving order
            tag_list = list(dict.fromkeys(tag_list))

        # Add 'short' tag for posts with 200 words or fewer
        if word_count <= 200 and 'short' not in tag_list:
            tag_list.append('short')

        # Sort tags alphabetically, but keep 'short' first if present
        if 'short' in tag_list:
            tag_list.remove('short')
            tag_list.sort()
            tag_list.insert(0, 'short')
        else:
            tag_list.sort()

        return ", ".join(tag_list) if tag_list else "null"

    def generate_html_output(self, post: BlogPost) -> None:
        """Generate HTML output from blog post using template."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")

        try:
            with open(self.template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()
        except IOError as e:
            raise RuntimeError(f"Failed to read template: {e}")

        # Prepare replacements with proper HTML escaping for title
        escaped_title = post.title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        tag_field = f'<tags:{post.tags}>' if post.tags != "null" else '<tags:>'
        
        replacements = {
            'blog</a> / ': f'blog</a> / {escaped_title}',
            '</p>': f'{post.body}</p>',
            '<word count:> <tags:>': f'<word count:{post.word_count}> {tag_field}',
        }

        # Add publish date if available
        if post.publish_date:
            try:
                date_str = self.timestamp_to_readable(post.publish_date)
                replacements['date-created"></span>'] = f'date-created">{date_str}</span>'
            except ValueError as e:
                print(f"Warning: Could not format publish date: {e}")

        # Add update date if available
        if post.update_date:
            try:
                update_str = self.timestamp_to_readable(post.update_date)
                replacements['<i id="last-modified"></i>'] = (
                    f'<br /><i id="last-modified">last modified {update_str}</i>'
                )
            except ValueError as e:
                print(f"Warning: Could not format update date: {e}")

        # Apply replacements
        for old, new in replacements.items():
            template_content = template_content.replace(old, new)

        # Write output file
        output_path = self.blog_output_dir / f"{post.hyphenated_title}.html"
        self.blog_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(template_content)
            print(f"Generated HTML: {output_path}")
        except IOError as e:
            raise RuntimeError(f"Failed to write output file: {e}")

    def run_blog_generator(self) -> None:
        """Run the blog generator script."""
        try:
            if self.gen_blog_script.exists():
                result = subprocess.run(
                    ["python", str(self.gen_blog_script)], 
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    print("Blog generator output:", result.stdout.strip())
            else:
                print(f"Warning: Blog generator script not found: {self.gen_blog_script}")
        except subprocess.CalledProcessError as e:
            print(f"Error running blog generator (exit code {e.returncode}): {e.stderr}")
        except subprocess.TimeoutExpired:
            print("Blog generator timed out after 30 seconds")
        except Exception as e:
            print(f"Unexpected error running blog generator: {e}")

    def find_post_file(self, filename: str) -> Path:
        """Find and return the path to a post file."""
        # Check if it's already a full path
        full_path = Path(filename)
        if full_path.is_absolute() and full_path.exists():
            return full_path
        
        # First try exact match in blog_raw_dir
        exact_path = self.blog_raw_dir / filename
        if exact_path.exists():
            return exact_path
        
        # Then try glob pattern for more flexible matching
        search_pattern = str(self.blog_raw_dir / filename)
        files_found = glob.glob(search_pattern)
        
        if not files_found:
            # Try case-insensitive search
            all_files = list(self.blog_raw_dir.glob('*'))
            matches = [f for f in all_files if f.name.lower() == filename.lower()]
            if matches:
                return matches[0]
            
            # If it was a full path that doesn't exist, give a specific error
            if full_path.is_absolute():
                raise FileNotFoundError(f"File not found at full path: {filename}")
            
            raise FileNotFoundError(
                f"File '{filename}' not found in {self.blog_raw_dir}. "
                f"Available files: {[f.name for f in all_files if f.is_file()]}"
            )
        
        return Path(files_found[0])

    def process_post(self, action: PostAction, filename: str) -> bool:
        """Main method to process a blog post. Returns True if successful."""
        try:
            # Find the post file
            file_path = self.find_post_file(filename)
            print(f"Found file: {file_path}")

            # Parse the post
            post = self.parse_post_file(file_path)

            # Handle different actions
            if action == PostAction.PUBLISH:
                if post.is_published:
                    readable_date = self.timestamp_to_readable(post.publish_date)
                    if not self.get_user_confirmation(
                        f"Post already published on {readable_date}. Overwrite publish date?"
                    ):
                        return False
                
                # Set publish date
                current_time = self.get_current_timestamp()
                self.update_field_in_file(file_path, "publish-date", current_time)
                post.publish_date = current_time
                print(f"Published post: {post.title}")

            elif action == PostAction.UPDATE:
                if not post.is_published:
                    print("Warning: Updating an unpublished post")
                
                # Set update date
                current_time = self.get_current_timestamp()
                self.update_field_in_file(file_path, "update-date", current_time)
                post.update_date = current_time
                print(f"Updated post: {post.title}")

            elif action == PostAction.REFRESH:
                print(f"Refreshing post: {post.title}")

            # Generate HTML output
            self.generate_html_output(post)

            # Run blog generator to update index
            self.run_blog_generator()
            
            return True

        except (FileNotFoundError, ValueError, RuntimeError) as e:
            print(f"Error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    def parse_command_line(self) -> tuple[PostAction, str]:
        """Parse command line arguments or get input from user."""
        if len(sys.argv) == 3:
            action_str, filename = sys.argv[1], sys.argv[2]
        else:
            try:
                user_input = input(
                    "Enter command (publish/update/refresh <filename_or_path>): "
                ).strip().split(maxsplit=1)  # Split on first space only
            except (EOFError, KeyboardInterrupt):
                raise KeyboardInterrupt("Operation cancelled by user")
            
            if len(user_input) != 2:
                raise ValueError(
                    "Invalid command format. Expected: <action> <filename>\n"
                    "Actions: publish, update, refresh"
                )
            
            action_str, filename = user_input[0], user_input[1]

        # Validate action
        try:
            action = PostAction(action_str.lower())
        except ValueError:
            valid_actions = [action.value for action in PostAction]
            raise ValueError(
                f"Invalid action: '{action_str}'. Must be one of: {', '.join(valid_actions)}"
            )

        return action, filename

    def run(self) -> None:
        """Main entry point for the script."""
        try:
            action, filename = self.parse_command_line()
            success = self.process_post(action, filename)
            if success:
                print("Operation completed successfully!")
            else:
                sys.exit(1)
        except (ValueError, KeyboardInterrupt) as e:
            if isinstance(e, KeyboardInterrupt):
                print("\nOperation cancelled by user")
            else:
                print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            sys.exit(1)


def main():
    """Main function."""
    processor = BlogPostProcessor()
    processor.run()


if __name__ == "__main__":
    main()
