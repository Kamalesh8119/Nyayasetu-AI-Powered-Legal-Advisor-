from app.db.database import get_pg_conn, release_pg_conn

def create_tables():
    conn = get_pg_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id         SERIAL PRIMARY KEY,
                    user_id    TEXT,
                    query      TEXT,
                    response   TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Group messages into conversations (rows saved before this have NULL)
            cur.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS session_id TEXT;")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_session
                ON chat_sessions (user_id, session_id, created_at);
            """)
        conn.commit()
    finally:
        release_pg_conn(conn)