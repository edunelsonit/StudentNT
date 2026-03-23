import streamlit as st
from database import init_db
from auth_lib import login, handle_callback
from ai_engine import generate_learning
from services import (
    register_user_if_not_exists,
    save_user_topic,
    get_user_topics
)

# Init DB
init_db()

st.set_page_config(page_title="Nutrition Platform")

# Auth
handle_callback()

if "user" not in st.session_state:
    login()
    st.stop()

user = st.session_state["user"]

# Register user in DB
register_user_if_not_exists(user)

st.title("🥗 Nutrition Learning Platform")
st.success(f"Welcome {user['name']}")

menu = st.sidebar.selectbox("Menu", ["Generate", "My Topics"])

# Generate
if menu == "Generate":
    country = st.text_input("Enter Your Country")
    topic = st.text_input("Enter Topic")

    if st.button("Generate"):
        content = generate_learning(country,topic)
        st.write(content)

        save_user_topic(user, country, topic, content)
        st.success("Saved")

# View Topics
elif menu == "My Topics":
    topics = get_user_topics(user)

    for t in topics:
        st.subheader(t[0])
        st.write(t[1])