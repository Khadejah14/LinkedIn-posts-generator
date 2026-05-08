from pydantic import BaseModel
from database.db import get_connection


class PostCreate(BaseModel):
    user_id: int
    content: str
    post_type: str = "post"  # 'post', 'draft', or 'link'


class Post(BaseModel):
    id: int
    user_id: int
    content: str
    post_type: str
    created_at: str


def save_post(post: PostCreate) -> Post:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO posts (user_id, content, post_type) VALUES (?, ?, ?)",
        (post.user_id, post.content, post.post_type),
    )
    conn.commit()
    post_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    return Post(
        id=row["id"],
        user_id=row["user_id"],
        content=row["content"],
        post_type=row["post_type"],
        created_at=row["created_at"],
    )


def get_posts(user_id: int, post_type: str | None = None) -> list[Post]:
    conn = get_connection()
    if post_type:
        rows = conn.execute(
            "SELECT * FROM posts WHERE user_id = ? AND post_type = ? ORDER BY created_at DESC",
            (user_id, post_type),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()
    conn.close()
    return [
        Post(
            id=r["id"],
            user_id=r["user_id"],
            content=r["content"],
            post_type=r["post_type"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def delete_post(post_id: int) -> bool:
    conn = get_connection()
    cursor = conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted
