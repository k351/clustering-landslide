import streamlit as st

from components.auth import (
    check_admin_login,
    init_session,
    is_logged_in,
    login_user,
)
from components.sidebar import hide_default_nav, show_sidebar

st.set_page_config(
    page_title="Sistem Clustering Tanah Longsor",
    page_icon="🏔️",
    layout="wide",
)

init_session()
hide_default_nav()

if not is_logged_in():
    hide_default_nav(hide_sidebar=True)

    st.title("Sistem Clustering Tanah Longsor")
    st.write("Silakan masuk untuk melihat hasil pengelompokan wilayah.")

    login_option = st.radio(
        "Pilih cara masuk:",
        ["Login sebagai Admin", "Masuk sebagai Guest"],
        horizontal=True,
    )

    if login_option == "Login sebagai Admin":
        st.subheader("Login Admin")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    st.warning("Harap isi username dan password.")
                elif check_admin_login(username, password):
                    login_user(username, "admin")
                    st.rerun()
                else:
                    st.error("Username atau password salah.")
    else:
        st.subheader("Masuk sebagai Guest")
        st.info(
            "Sebagai guest Anda dapat melihat hasil clustering, "
            "tetapi tidak dapat mengunggah atau mengubah data."
        )
        if st.button("Masuk sebagai Guest", use_container_width=True):
            login_user("Guest", "guest")
            st.rerun()

    st.stop()

show_sidebar()

role_label = "Admin" if st.session_state.user_type == "admin" else "Guest"
st.title("Sistem Clustering Tanah Longsor")
st.markdown(f"Halo, **{st.session_state.username}** ({role_label}).")

st.markdown(
    """
    **Tanah longsor** merupakan salah satu bencana alam yang dapat terjadi
    di berbagai wilayah Indonesia, terutama pada wilayah dengan lereng rentan
    dan curah hujan tinggi. Dampaknya dapat meliputi korban jiwa, korban terdampak,
    kerusakan rumah, serta kerusakan infrastruktur.

    Dashboard ini mengelompokkan wilayah berdasarkan karakteristik dampak tanah
    longsor menggunakan algoritma **K-Medoids** dan **OPTICS**.
    """
)

if st.session_state.user_type == "guest":
    st.warning("Mode guest: data hanya dapat dilihat, tidak dapat diunggah atau diubah.")
else:
    st.success("Mode admin: Anda dapat mengelola data dan menjalankan clustering.")

st.subheader("Dokumentasi Tanah Longsor")
st.image(
    "./images/Tanah longsor.jpg",
    caption="Dampak tanah longsor terhadap permukiman warga.",
    use_container_width=True,
)

st.subheader("Mulai analisis")
col1, col2 = st.columns(2)
with col1:
    if st.button("Buka Clustering", use_container_width=True):
        st.switch_page("pages/Clustering.py")
with col2:
    data_label = "Kelola Data" if st.session_state.user_type == "admin" else "Lihat Data"
    if st.button(data_label, use_container_width=True):
        st.switch_page("pages/Data.py")