from models import save_topic, get_all_accessible_topics, create_user, get_user

def register_user_if_not_exists(userinfo):
    email = userinfo.get("email")
    name = userinfo.get("name")
    if not get_user(email):
        # Default new users to student; manual DB update needed for admin
        create_user(email, name, role="student")

def save_user_topic(user_email, country, topic, content):
    save_topic(user_email, country, topic, content, is_global=0)

def get_user_topics_list(user_email):
    # Fixed: This now expects the email string directly
    return get_all_accessible_topics(user_email)