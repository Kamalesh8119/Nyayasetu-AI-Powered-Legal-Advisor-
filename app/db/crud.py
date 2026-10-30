import hashlib
from psycopg2.extras import RealDictCursor
from app.db.database import get_pg_conn, release_pg_conn, redis_client
from app.utils.config import REDIS_CACHE_TTL



# Rows saved before conversations existed have no session_id; each one is
# exposed as its own conversation with id "legacy-<row id>".
SESSION_KEY = "COALESCE(session_id, 'legacy-' || id)"


def save_chat(user_id: str, query: str, response: str, session_id: str | None = None):
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, query, response, session_id)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, query, response, session_id),
            )
        conn.commit()
    finally:
        release_pg_conn(conn)


def list_sessions(user_id: str, limit: int = 50) -> list:
    """Conversations for a user, most recent first, titled by their first question."""
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT {SESSION_KEY} AS session_id,
                       (ARRAY_AGG(query ORDER BY created_at, id))[1] AS title,
                       COUNT(*) AS message_count,
                       MAX(created_at) AS updated_at
                FROM chat_sessions
                WHERE user_id = %s
                GROUP BY 1
                ORDER BY updated_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return cur.fetchall()
    finally:
        release_pg_conn(conn)


def get_session_messages(user_id: str, session_id: str) -> list:
    conn = get_pg_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT query, response, created_at
                FROM chat_sessions
                WHERE user_id = %s AND {SESSION_KEY} = %s
                ORDER BY created_at, id
                """,
                (user_id, session_id),
            )
            return cur.fetchall()
    finally:
        release_pg_conn(conn)


def _cache_key(query: str) -> str:
    """Stable cache key from query text."""
    return "nyayasetu:query:" + hashlib.sha256(query.strip().lower().encode()).hexdigest()


def get_cached_response(query: str) -> str | None:
    """Return cached LLM response or None if cache miss."""
    return redis_client.get(_cache_key(query))


def set_cached_response(query: str, response: str):
    """Cache LLM response with TTL."""
    redis_client.setex(_cache_key(query), REDIS_CACHE_TTL, response)