import hmac
import bcrypt
import streamlit as st
from sqlalchemy import create_engine, text

SESSION_DEFAULTS = {
    "logged_in": False,
    "user_type": None,
    "username": None,
}

def init_session():
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
def is_logged_in():
    init_session()
    return bool(st.session_state.logged_in)

def require_login():
    if not is_logged_in():
        st.switch_page("Home.py")
        
def login_user(username, user_type):
    st.session_state.logged_in = True
    st.session_state.user_type = user_type
    st.session_state.username = username
    
def logout_user():
    for key, value in SESSION_DEFAULTS.items():
        st.session_state[key] = value
        
def is_admin():
    return is_logged_in() and st.session_state.user_type == "admin"

def _connection_string():
    raw = st.secrets["connection_string"]
    return raw.replace("postgresql://", "postgresql+psycopg2://", 1)

@st.cache_resource
def get_engine():
    return create_engine(_connection_string(), pool_pre_ping=True)

def _password_matches(plain_password, stored_password):
    stored = str(stored_password or "")
    if stored.startswith("$2"):
        try:
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                stored.encode("utf-8"),
            )
        except ValueError:
            return False
    return hmac.compare_digest(plain_password, stored)

def check_admin_login(username, password):
    lookups = [
        text('SELECT "username", "password" FROM "Users" WHERE "username" = :username'),
        text("SELECT username, password FROM admin WHERE username = :username"),
    ]
    try:
        engine = get_engine()
        with engine.connect() as conn:
            for query in lookups:
                try:
                    row = conn.execute(query, {"username": username}).fetchone()
                except Exception:
                    continue
                if row is not None:
                    return _password_matches(password, row[1])
        return False
    except Exception as exc:
        st.error("Gagal terhubung ke database. Coba lagi nanti.")
        st.caption(str(exc))
        return False