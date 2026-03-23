import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
from config import settings


def login():
    oauth = OAuth2Session(
        settings.AUTH0_CLIENT_ID,
        settings.AUTH0_CLIENT_SECRET,
        scope="openid profile email"
    )

    authorization_url, state = oauth.create_authorization_url(
        f"https://{settings.AUTH0_DOMAIN}/authorize",
        redirect_uri=settings.AUTH0_CALLBACK_URL
    )

    st.session_state["oauth_state"] = state

    st.markdown(f"[Login with Auth0]({authorization_url})")


def handle_callback():
    if "user" in st.session_state:
        return

    if "code" in st.query_params:
        code = st.query_params["code"]

        oauth = OAuth2Session(
            settings.AUTH0_CLIENT_ID,
            settings.AUTH0_CLIENT_SECRET,
            state=st.session_state.get("oauth_state")
        )

        token = oauth.fetch_token(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            code=code,
            redirect_uri=settings.AUTH0_CALLBACK_URL,
            client_secret=settings.AUTH0_CLIENT_SECRET
        )

        userinfo = oauth.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo"
        ).json()

        st.session_state["user"] = userinfo

        # Prevent reuse error
        st.query_params.clear()