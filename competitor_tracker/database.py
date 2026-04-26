"""SQLite database for competitor tracking."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import asdict


DB_PATH = Path(__file__).parent / "competitor_tracker.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            profile_url TEXT UNIQUE NOT NULL,
            industry TEXT,
            followers INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER NOT NULL,
            post_id TEXT,
            content TEXT NOT NULL,
            hook TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            impressions INTEGER DEFAULT 0,
            posted_at TIMESTAMP,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            url TEXT,
            FOREIGN KEY (competitor_id) REFERENCES competitors(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            hook_type TEXT,
            topic TEXT,
            tone TEXT,
            emotional_appeal TEXT,
            content_format TEXT,
            viral_patterns TEXT,
            cta_type TEXT,
            structure TEXT,
            word_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_name TEXT NOT NULL,
            frequency INTEGER DEFAULT 0,
            competitors_using TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT UNIQUE NOT NULL,
            frequency INTEGER DEFAULT 0,
            last_posted TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER,
            status TEXT,
            error_message TEXT,
            posts_fetched INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_posts_competitor ON posts(competitor_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_posts_posted ON posts(posted_at)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_analysis_post ON post_analysis(post_id)
    """)

    conn.commit()
    conn.close()


def add_competitor(name: str, profile_url: str, industry: str = None, followers: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO competitors (name, profile_url, industry, followers)
            VALUES (?, ?, ?, ?)
        """, (name, profile_url, industry, followers))
        conn.commit()
        competitor_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM competitors WHERE profile_url = ?", (profile_url,))
        competitor_id = cursor.fetchone()[0]
        cursor.execute("""
            UPDATE competitors SET name = ?, industry = ?, followers = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, industry, followers, competitor_id))
        conn.commit()
    finally:
        conn.close()
    return competitor_id


def get_competitors() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitors ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_competitor(competitor_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM post_analysis WHERE post_id IN (SELECT id FROM posts WHERE competitor_id = ?)", (competitor_id,))
    cursor.execute("DELETE FROM posts WHERE competitor_id = ?", (competitor_id,))
    cursor.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))
    conn.commit()
    conn.close()


def add_post(competitor_id: int, post_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (competitor_id, post_id, content, hook, likes, comments, shares, impressions, posted_at, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        competitor_id,
        post_data.get("post_id"),
        post_data.get("content", ""),
        post_data.get("hook", ""),
        post_data.get("likes", 0),
        post_data.get("comments", 0),
        post_data.get("shares", 0),
        post_data.get("impressions", 0),
        post_data.get("posted_at"),
        post_data.get("url")
    ))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id


def get_posts(competitor_id: int = None, limit: int = 100) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if competitor_id:
        cursor.execute("""
            SELECT p.*, c.name as competitor_name
            FROM posts p
            JOIN competitors c ON p.competitor_id = c.id
            WHERE p.competitor_id = ?
            ORDER BY p.posted_at DESC
            LIMIT ?
        """, (competitor_id, limit))
    else:
        cursor.execute("""
            SELECT p.*, c.name as competitor_name
            FROM posts p
            JOIN competitors c ON p.competitor_id = c.id
            ORDER BY p.posted_at DESC
            LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_analysis(post_id: int, analysis: dict) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO post_analysis (
            post_id, hook_type, topic, tone, emotional_appeal,
            content_format, viral_patterns, cta_type, structure, word_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        post_id,
        analysis.get("hook_type"),
        analysis.get("topic"),
        analysis.get("tone"),
        analysis.get("emotional_appeal"),
        analysis.get("content_format"),
        json.dumps(analysis.get("viral_patterns", [])),
        analysis.get("cta_type"),
        analysis.get("structure"),
        analysis.get("word_count")
    ))
    conn.commit()
    conn.close()


def get_analysis(post_id: int) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM post_analysis WHERE post_id = ?", (post_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def get_all_analysis(competitor_id: int = None) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if competitor_id:
        cursor.execute("""
            SELECT a.*, p.content, p.hook, p.likes, p.competitor_id, c.name as competitor_name
            FROM post_analysis a
            JOIN posts p ON a.post_id = p.id
            JOIN competitors c ON p.competitor_id = c.id
            WHERE p.competitor_id = ?
            ORDER BY p.likes DESC
        """, (competitor_id,))
    else:
        cursor.execute("""
            SELECT a.*, p.content, p.hook, p.likes, p.competitor_id, c.name as competitor_name
            FROM post_analysis a
            JOIN posts p ON a.post_id = p.id
            JOIN competitors c ON p.competitor_id = c.id
            ORDER BY p.likes DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_top_posts(limit: int = 10) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, c.name as competitor_name
        FROM posts p
        JOIN competitors c ON p.competitor_id = c.id
        ORDER BY (p.likes + p.comments * 2 + p.shares * 3) DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_trends(analysis_data: list[dict]) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    topic_counts: dict[str, int] = {}
    hook_type_counts: dict[str, int] = {}
    tone_counts: dict[str, int] = {}

    for analysis in analysis_data:
        topic = analysis.get("topic", "Unknown")
        hook_type = analysis.get("hook_type", "Unknown")
        tone = analysis.get("tone", "Unknown")

        topic_counts[topic] = topic_counts.get(topic, 0) + 1
        hook_type_counts[hook_type] = hook_type_counts.get(hook_type, 0) + 1
        tone_counts[tone] = tone_counts.get(tone, 0) + 1

    for topic, count in topic_counts.items():
        cursor.execute("""
            INSERT INTO trends (trend_name, frequency, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(trend_name) DO UPDATE SET
                frequency = frequency + ?,
                last_seen = CURRENT_TIMESTAMP
        """, (topic, count, count))

    conn.commit()
    conn.close()


def get_trends() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trends ORDER BY frequency DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_user_topic(topic: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_topics (topic, frequency, last_posted)
        VALUES (?, 1, CURRENT_TIMESTAMP)
        ON CONFLICT(topic) DO UPDATE SET
            frequency = frequency + 1,
            last_posted = CURRENT_TIMESTAMP
    """, (topic,))
    conn.commit()
    conn.close()


def get_user_topics() -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_topics ORDER BY frequency DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_scrape_log(competitor_id: int, status: str, error_message: str = None, posts_fetched: int = 0) -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scrape_logs (competitor_id, status, error_message, posts_fetched)
        VALUES (?, ?, ?, ?)
    """, (competitor_id, status, error_message, posts_fetched))
    conn.commit()
    conn.close()


def get_scrape_logs(limit: int = 20) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sl.*, c.name as competitor_name
        FROM scrape_logs sl
        LEFT JOIN competitors c ON sl.competitor_id = c.id
        ORDER BY sl.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM competitors")
    competitors_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts")
    posts_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(likes) FROM posts")
    total_likes = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(comments) FROM posts")
    total_comments = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT c.name, COUNT(p.id) as post_count, SUM(p.likes) as total_likes
        FROM competitors c
        LEFT JOIN posts p ON c.id = p.competitor_id
        GROUP BY c.id
    """)
    competitor_stats = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        "competitors_count": competitors_count,
        "posts_count": posts_count,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "competitor_stats": competitor_stats
    }
