"""
Database module for storing chat conversations
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")


def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_calls TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_customer_session 
        ON conversations (customer_id, session_id)
    """)

    # Create payload table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payload (
            customer_id TEXT,
            payload TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at: {DB_PATH}")


def save_message(customer_id: str, session_id: str, role: str, content: str, agent_calls: List[str] = None):
    """
    Save a message to the database

    Args:
        customer_id: Customer ID
        session_id: Session ID (use customer_id if no session)
        role: 'user' or 'assistant'
        content: Message content
        agent_calls: List of agent tools called (for assistant messages)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    agent_calls_json = json.dumps(agent_calls) if agent_calls else None

    cursor.execute("""
        INSERT INTO conversations (customer_id, session_id, role, content, agent_calls)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, session_id, role, content, agent_calls_json))

    conn.commit()
    conn.close()


def get_conversation_history(customer_id: str, session_id: str = None, limit: int = 50) -> List[Dict]:
    """
    Get conversation history for a customer

    Args:
        customer_id: Customer ID
        session_id: Optional session ID (defaults to customer_id)
        limit: Maximum number of messages to retrieve

    Returns:
        List of messages in format: [{"role": "user/assistant", "content": "..."}]
    """
    if session_id is None:
        session_id = customer_id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content, agent_calls, timestamp
        FROM conversations
        WHERE customer_id = ? AND session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (customer_id, session_id, limit))

    rows = cursor.fetchall()
    conn.close()

    # Reverse to get chronological order
    messages = []
    for row in reversed(rows):
        messages.append({
            "role": row[0],
            "content": row[1]
        })

    return messages


def clear_conversation_history(customer_id: str, session_id: str = None):
    """
    Clear conversation history for a customer

    Args:
        customer_id: Customer ID
        session_id: Optional session ID (defaults to customer_id)
    """
    if session_id is None:
        session_id = customer_id

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM conversations
        WHERE customer_id = ? AND session_id = ?
    """, (customer_id, session_id))

    conn.commit()
    conn.close()


def get_conversation_stats(customer_id: str) -> Dict:
    """
    Get conversation statistics for a customer

    Args:
        customer_id: Customer ID

    Returns:
        Dictionary with stats: total_messages, sessions, etc.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total messages
    cursor.execute("""
        SELECT COUNT(*) FROM conversations WHERE customer_id = ?
    """, (customer_id,))
    total_messages = cursor.fetchone()[0]

    # Number of sessions
    cursor.execute("""
        SELECT COUNT(DISTINCT session_id) FROM conversations WHERE customer_id = ?
    """, (customer_id,))
    total_sessions = cursor.fetchone()[0]

    # Last conversation time
    cursor.execute("""
        SELECT MAX(timestamp) FROM conversations WHERE customer_id = ?
    """, (customer_id,))
    last_conversation = cursor.fetchone()[0]

    conn.close()

    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "last_conversation": last_conversation
    }


# Initialize database on module import
init_database()
