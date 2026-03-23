from models import save_topic, get_all_accessible_topics, create_user, get_user

def register_user_if_not_exists(userinfo):
    email, name = userinfo.get("email"), userinfo.get("name")
    if not get_user(email): create_user(email, name)

def save_user_topic(email, country, topic, content):
    save_topic(email, country, topic, content, is_global=0)

def get_user_topics_list(email):
    return get_all_accessible_topics(email)