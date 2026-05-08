"""Example usage of the database layer."""

from database.db import init_db
from models.user import UserCreate, create_user, get_user, list_users
from models.post import PostCreate, save_post, get_posts, delete_post


def main():
    init_db()
    print("Database initialized.\n")

    # Create a user
    user = create_user(UserCreate(name="Kadej"))
    print(f"Created user: {user}")

    # Save some posts
    post1 = save_post(PostCreate(user_id=user.id, content="I was lonely for years", post_type="post"))
    post2 = save_post(PostCreate(user_id=user.id, content="Don't Try", post_type="post"))
    draft1 = save_post(PostCreate(user_id=user.id, content="I like being alone...", post_type="draft"))
    link1 = save_post(PostCreate(user_id=user.id, content="https://markmanson.net/how-to-be-happy", post_type="link"))
    print(f"Saved {4} items for user '{user.name}'\n")

    # Fetch all posts
    all_items = get_posts(user.id)
    print(f"All items ({len(all_items)}):")
    for p in all_items:
        print(f"  [{p.post_type}] {p.content[:50]}")

    # Fetch only drafts
    drafts = get_posts(user.id, post_type="draft")
    print(f"\nDrafts only ({len(drafts)}):")
    for d in drafts:
        print(f"  {d.content[:50]}")

    # Delete a post
    deleted = delete_post(post1.id)
    print(f"\nDeleted post {post1.id}: {deleted}")

    # Verify
    remaining = get_posts(user.id)
    print(f"Remaining items: {len(remaining)}")

    # List users
    users = list_users()
    print(f"\nAll users: {users}")


if __name__ == "__main__":
    main()
