from models import save_topic, get_topics, create_user, get_user


def register_user_if_not_exists(userinfo):
    email = userinfo.get("email")
    name = userinfo.get("name")

    existing = get_user(email)

    if not existing:
        create_user(email, name, role="student")


def save_user_topic(user, country, topic, content):
    save_topic(user["email"], country, topic, content)


def get_user_topics(user):
    return get_topics(user["email"])