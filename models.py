from database import get_connection

def create_user(email, name, role="student"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, name, role) VALUES (?, ?, ?)", (email, name, role))
    conn.commit()
    conn.close()

def get_user(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    return user

def is_admin(email):
    user = get_user(email)
    return user is not None and user[3] == "admin"

def save_topic(user_email, country, topic, content, is_global=0):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO topics (user_email, country, topic, content, is_global) VALUES (?, ?, ?, ?, ?)",
        (user_email, country, topic, content, is_global)
    )
    conn.commit()
    conn.close()

def get_all_accessible_topics(user_email):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT topic, content, country, is_global FROM topics WHERE user_email=? OR is_global=1 ORDER BY is_global DESC",
        (user_email,)
    )
    data = c.fetchall()
    conn.close()
    return data