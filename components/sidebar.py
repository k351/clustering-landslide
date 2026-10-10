import streamlit as st

from components.auth import logout_user

def hide_default_nav(hide_sidebar=False):
    sidebar_rule = "[data-testid='stSidebar'] { display: none; }" if hide_sidebar else ""
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{ display: none; }}
            [data-testid="stSidebar"] {{ padding-top: 0rem; }}
            {sidebar_rule}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_sidebar():
    hide_default_nav()

    st.sidebar.markdown(
        "<h1 style='text-align: center; font-size: 1.85rem;'>Dashboard</h1>",
        unsafe_allow_html=True,
    )

    if st.sidebar.button("Home", use_container_width=True):
        st.switch_page("Home.py")

    if st.sidebar.button("Clustering", use_container_width=True):
        st.switch_page("pages/Clustering.py")

    if st.sidebar.button("Data", use_container_width=True):
        st.switch_page("pages/Data.py")

    if st.sidebar.button("FAQ", use_container_width=True):
        st.switch_page("pages/FAQ.py")

    if st.sidebar.button("About", use_container_width=True):
        st.switch_page("pages/About.py")

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout", use_container_width=True):
        logout_user()
        st.switch_page("Home.py")
