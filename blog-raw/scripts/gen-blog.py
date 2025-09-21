#!/usr/bin/env python3
"""
Blog index generator script.
Extracts metadata from HTML blog posts and generates the main blog index page.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class BlogEntry:
    """Data class representing a blog entry with metadata."""
    filename: str
    title: str
    date_created: str
    word_count: int
    tags: str
    
    @property
    def is_short_post(self) -> bool:
        """Check if this is a short post based on tags."""
        return 'short' in self.tags.lower()
    
    @property
    def parsed_date(self) -> datetime:
        """Parse the date string into a datetime object for sorting."""
        try:
            return datetime.strptime(self.date_created, '%b %d %y %I:%M%p')
        except ValueError as e:
            logger.warning(f"Failed to parse date '{self.date_created}' for {self.filename}: {e}")
            # Return a very old date as fallback
            return datetime(1900, 1, 1)
    
    @property
    def display_date(self) -> str:
        """Get the display date (first 9 characters)."""
        return self.date_created[:9]
    
    @property
    def tag_list(self) -> List[str]:
        """Get tags as a sorted list."""
        if not self.tags or self.tags.lower() == "none":
            return []
        
        tags = [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        
        # Sort with 'short' first if present
        if 'short' in tags:
            tags.remove('short')
            tags.sort()
            tags.insert(0, 'short')
        else:
            tags.sort()
            
        return tags


class BlogMetadataExtractor:
    """Handles extraction of metadata from HTML blog files."""
    
    # Regex patterns for extracting metadata
    PATTERNS = {
        'word_count': re.compile(r"<!-- <word count:(\d+)>"),
        'date_created': re.compile(r'id="date-created">(.*?)<'),
        'title': re.compile(r'<a href="\.\./blog\.html">blog<\/a> / (.*?)<\/h2>'),
        'tags': re.compile(r'<!-- <word count:\d+> <tags:(.*?)>-->')
    }
    
    def extract_blog_metadata(self, html_content: str) -> Dict[str, Any]:
        """Extract blog metadata from HTML content."""
        metadata = {}
        
        # Extract word count
        word_count_match = self.PATTERNS['word_count'].search(html_content)
        metadata['word_count'] = int(word_count_match.group(1)) if word_count_match else 0
        
        # Extract date created
        date_match = self.PATTERNS['date_created'].search(html_content)
        metadata['date_created'] = date_match.group(1) if date_match else None
        
        # Extract title
        title_match = self.PATTERNS['title'].search(html_content)
        metadata['title'] = title_match.group(1) if title_match else None
        
        # Extract tags
        tags_match = self.PATTERNS['tags'].search(html_content)
        metadata['tags'] = tags_match.group(1).strip() if tags_match else "none"
        
        return metadata
    
    def extract_from_file(self, filepath: Path) -> Optional[BlogEntry]:
        """Extract metadata from a single HTML file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                
            metadata = self.extract_blog_metadata(content)
            
            # Only create entry if we have essential data
            if metadata['title'] and metadata['date_created']:
                return BlogEntry(
                    filename=filepath.name,
                    title=metadata['title'],
                    date_created=metadata['date_created'],
                    word_count=metadata['word_count'],
                    tags=metadata['tags']
                )
            else:
                logger.warning(f"Skipping {filepath.name}: missing title or date")
                return None
                
        except IOError as e:
            logger.error(f"Failed to read file {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            return None


class BlogCardFormatter:
    """Handles formatting of blog entries into HTML cards."""
    
    def format_tag_list(self, tags: List[str]) -> str:
        """Format a list of tags into HTML spans."""
        if not tags:
            return ""
        
        formatted_tags = []
        for tag in tags:
            if tag == "short":
                formatted_tags.append(f'<span class="tag-label minipost">{tag}</span>')
            else:
                formatted_tags.append(f'<span class="tag-label">{tag}</span>')
        
        return ", ".join(formatted_tags)
    
    def format_single_card(self, entry: BlogEntry) -> str:
        """Format a single blog entry as an HTML card."""
        tag_html = self.format_tag_list(entry.tag_list)
        
        card_html = f'''<div class="card">
    <a href="blog/{entry.filename}">{entry.title}</a>
    <p>{entry.display_date}, {entry.word_count} words<br>{tag_html}</p>
</div>'''
        
        return card_html.strip()
    
    def format_all_cards(self, entries: List[BlogEntry]) -> str:
        """Format all blog entries as HTML cards, sorted by date."""
        # Sort entries by date (newest first)
        sorted_entries = sorted(entries, key=lambda x: x.parsed_date, reverse=True)
        
        # Format each entry as a card
        cards = [self.format_single_card(entry) for entry in sorted_entries]
        
        return "\n".join(cards)


class BlogPageUpdater:
    """Handles updating the main blog page with new content."""
    
    CONTAINER_PATTERN = re.compile(
        r'(<div[^>]*\bid="container"[^>]*>)(.*?)(</div>)',
        flags=re.DOTALL | re.IGNORECASE
    )
    
    def update_blog_page(self, blog_page_path: Path, card_html: str) -> None:
        """Update the main blog page with new card content."""
        try:
            with open(blog_page_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Find the container div
            match = self.CONTAINER_PATTERN.search(content)
            if not match:
                raise ValueError(f"Could not find container div in {blog_page_path}")
            
            # Replace container content
            new_container = f"{match.group(1)}\n{card_html}\n{match.group(3)}"
            new_content = content[:match.start()] + new_container + content[match.end():]
            
            # Write updated content
            with open(blog_page_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            logger.info(f"Updated {blog_page_path} with {len(card_html.split('</div>'))-1} blog entries")
            
        except IOError as e:
            raise RuntimeError(f"Failed to update blog page: {e}")
    
    def update_post_titles(self, blog_dir: Path, entries: List[BlogEntry]) -> None:
        """Update <title> tags in individual blog post HTML files."""
        updated_count = 0
        
        for entry in entries:
            filepath = blog_dir / entry.filename
            
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                new_title_tag = f"<title>{entry.title}</title>"
                
                # Replace existing title or add new one
                if "<title>" in content:
                    content = re.sub(
                        r"<title>.*?</title>", 
                        new_title_tag, 
                        content, 
                        flags=re.IGNORECASE
                    )
                else:
                    content = re.sub(
                        r"(<head[^>]*>)", 
                        rf"\1\n{new_title_tag}", 
                        content, 
                        flags=re.IGNORECASE
                    )
                
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                
                updated_count += 1
                
            except IOError as e:
                logger.error(f"Failed to update title in {filepath}: {e}")
            except Exception as e:
                logger.error(f"Error updating title in {filepath}: {e}")
        
        logger.info(f"Updated <title> tags in {updated_count} blog post files")


class BlogIndexGenerator:
    """Main class that orchestrates the blog index generation process."""
    
    def __init__(self, 
                 blog_dir: str = "C:\\FILESC\\cs\\mysite\\blog",
                 blog_page_path: str = "C:\\FILESC\\cs\\mysite\\blog.html"):
        """Initialize the blog generator with paths."""
        self.blog_dir = Path(blog_dir)
        self.blog_page_path = Path(blog_page_path)
        
        # Initialize components
        self.extractor = BlogMetadataExtractor()
        self.formatter = BlogCardFormatter()
        self.updater = BlogPageUpdater()
        
        # Validate paths
        self._validate_paths()
    
    def _validate_paths(self) -> None:
        """Validate that required paths exist."""
        if not self.blog_dir.exists():
            raise FileNotFoundError(f"Blog directory not found: {self.blog_dir}")
        
        if not self.blog_page_path.exists():
            raise FileNotFoundError(f"Blog page not found: {self.blog_page_path}")
    
    def extract_all_entries(self) -> List[BlogEntry]:
        """Extract metadata from all HTML files in the blog directory."""
        entries = []
        html_files = list(self.blog_dir.glob("*.html"))
        
        if not html_files:
            logger.warning(f"No HTML files found in {self.blog_dir}")
            return entries
        
        logger.info(f"Processing {len(html_files)} HTML files...")
        
        for filepath in html_files:
            entry = self.extractor.extract_from_file(filepath)
            if entry:
                entries.append(entry)
        
        logger.info(f"Successfully extracted metadata from {len(entries)} blog posts")
        return entries
    
    def generate_blog_index(self) -> None:
        """Main method to generate the blog index."""
        try:
            # Extract metadata from all blog posts
            entries = self.extract_all_entries()
            
            if not entries:
                logger.warning("No valid blog entries found")
                return
            
            # Update individual post titles
            self.updater.update_post_titles(self.blog_dir, entries)
            
            # Format entries as cards
            card_html = self.formatter.format_all_cards(entries)
            
            # Update the main blog page
            self.updater.update_blog_page(self.blog_page_path, card_html)
            
            # Print summary
            short_posts = sum(1 for entry in entries if entry.is_short_post)
            regular_posts = len(entries) - short_posts
            
            logger.info(f"Blog index generated successfully:")
            logger.info(f"  - {regular_posts} regular posts")
            logger.info(f"  - {short_posts} short posts")
            logger.info(f"  - Total: {len(entries)} posts")
            
        except Exception as e:
            logger.error(f"Failed to generate blog index: {e}")
            raise


def main():
    """Main entry point for the script."""
    try:
        generator = BlogIndexGenerator()
        generator.generate_blog_index()
    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
