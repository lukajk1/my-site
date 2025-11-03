from bs4 import BeautifulSoup

BLOG_PAGE = "blog.html"
HOME_PAGE = "index.html"
numberOfPosts = 9

def update_latest_posts(blog_file, home_file):
    try:
        # Read the blog file
        with open(blog_file, 'r', encoding='utf-8') as f:
            blog_soup = BeautifulSoup(f, 'html.parser')

        # Find the posts list and get the first 5 items
        blog_posts_ul = blog_soup.find(id='posts')
        if not blog_posts_ul:
            print(f"Error: Could not find 'posts' list in {blog_file}")
            return
            
        first_five_posts = blog_posts_ul.find_all('li', limit=numberOfPosts)

        # Read the home file
        with open(home_file, 'r', encoding='utf-8') as f:
            home_soup = BeautifulSoup(f, 'html.parser')

        # Find the latest posts list
        latest_posts_ul = home_soup.find(id='latest-posts')
        if not latest_posts_ul:
            print(f"Error: Could not find 'latest-posts' list in {home_file}")
            return

        # Clear existing content and append the new posts
        latest_posts_ul.clear()
        for post in first_five_posts:
            latest_posts_ul.append(post)

        # Write the changes back to the home file
        with open(home_file, 'w', encoding='utf-8') as f:
            f.write(str(home_soup))

        print(f"Successfully updated 'latest-posts' in {home_file}")

    except FileNotFoundError:
        print("Error: One of the files was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_latest_posts(BLOG_PAGE, HOME_PAGE)
