import streamlit as st

from components.auth import logout_user

def hide_default_nav(hide_sidebar=False):
    sidebar_rule = (
        "[data-testid='stSidebar'] { display: none; }"
        if hide_sidebar
        else ""
    )

    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                display: none;
            }}

            {sidebar_rule}
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_sidebar(active_page=None):
    hide_default_nav()

    st.sidebar.title("Dashboard")
    st.sidebar.divider()

    pages = [
        ("Beranda", "Home.py", "Home", ":material/home:"),
        ("Clustering", "pages/Clustering.py", "Clustering", ":material/analytics:"),
        ("Data", "pages/Data.py", "Data", ":material/database:"),
        ("FAQ", "pages/FAQ.py", "FAQ", ":material/help_outline:"),
        ("Tentang", "pages/About.py", "About", ":material/info:"),
    ]

    for label, page_path, page_name, icon in pages:
        if st.sidebar.button(
            label,
            key=f"nav_{page_name.lower()}",
            icon=icon,
            use_container_width=True,
            type="primary" if active_page == page_name else "secondary",
        ):
            st.switch_page(page_path)

    st.sidebar.divider()

    if st.sidebar.button(
        "Logout",
        key="sidebar_logout",
        icon=":material/logout:",
        use_container_width=True,
    ):
        logout_user()
        st.switch_page("Home.py")