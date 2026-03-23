import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from config import settings

def login():
    oauth = OAuth2Session(settings.AUTH0_CLIENT_ID, settings.AUTH0_CLIENT_SECRET, scope="openid profile email")
    authorization_url, state = oauth.create_authorization_url(f"https://{settings.AUTH0_DOMAIN}/authorize", redirect_uri=settings.AUTH0_CALLBACK_URL)
    st.session_state["oauth_state"] = state
    st.markdown(f"### [Click here to Login]({authorization_url})")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    logout_url = (f"https://{settings.AUTH0_DOMAIN}/v2/logout?client_id={settings.AUTH0_CLIENT_ID}&returnTo={settings.AUTH0_CALLBACK_URL}")
    st.markdown(f'<meta http-equiv="refresh" content="0;url={logout_url}">', unsafe_allow_html=True)
    st.stop()

def handle_callback():
    if "user" not in st.session_state and "code" in st.query_params:
        oauth = OAuth2Session(settings.AUTH0_CLIENT_ID, settings.AUTH0_CLIENT_SECRET, state=st.session_state.get("oauth_state"))
        token = oauth.fetch_token(f"https://{settings.AUTH0_DOMAIN}/oauth/token", code=st.query_params["code"], redirect_uri=settings.AUTH0_CALLBACK_URL)
        userinfo = oauth.get(f"https://{settings.AUTH0_DOMAIN}/userinfo").json()
        st.session_state["user"] = userinfo
        st.query_params.clear()