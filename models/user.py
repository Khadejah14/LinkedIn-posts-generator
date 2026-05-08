from pydantic import BaseModel
from database.db import get_connection


class UserCreate(BaseModel):
    name: str


class User(BaseModel):
    id: int
    name: str
    created_at: str


def create_user(user: UserCreate) -> User:
    conn = get_connection()
    cursor = conn.execute("INSERT INTO users (name) VALUES (?)", (user.name,))
    conn.commit()
    user_id = cursor.lastrowid
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return User(id=row["id"], name=row["name"], created_at=row["created_at"])


def get_user(user_id: int) -> User | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return User(id=row["id"], name=row["name"], created_at=row["created_at"])


def list_users() -> list[User]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [User(id=r["id"], name=r["name"], created_at=r["created_at"]) for r in rows]
