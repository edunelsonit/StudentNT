from database import get_connection

def create_user(email, name, role="student"):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "INSERT INTO users (email, name, role) VALUES (?, ?, ?)",
        (email, name, role)
    )

    conn.commit()
    conn.close()


def get_user(email):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()

    conn.close()
    return user

def save_topic(user_email, country,topic, content):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "INSERT INTO topics (user_email, country,topic, content) VALUES (?, ?, ?,?)",
        (user_email, country, topic, content)
    )

    conn.commit()
    conn.close()


def get_topics(user_email):
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "SELECT topic, content FROM topics WHERE user_email=?",
        (user_email,)
    )

    data = c.fetchall()
    conn.close()
    return data