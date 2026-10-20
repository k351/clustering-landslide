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


st.markdown("""
<style>
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }

    .login-header h2 {
        font-size: 26px !important;
        font-weight: 700 !important;
    }

    .login-header p {
        color: #94a3b8;
        font-size: 14px;
    }

    .home-hero {
        padding: 30px;
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 18px;
        margin-top: 20px;
        margin-bottom: 30px;
    }

    .home-eyebrow {
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 20px;
    }

    .home-title {
        font-size: 32px;
        font-weight: 750;
        line-height: 1.35;
        margin-bottom: 18px;
    }

    .home-description {
        font-size: 16px;
        line-height: 1.8;
        color: #b8b8bd;
    }

    .section-description {
        opacity: 0.75;
        line-height: 1.8;
        margin-bottom: 20px;
    }

    .home-footer {
        text-align: center;
        opacity: 0.6;
        font-size: 13px;
        line-height: 1.8;
        margin-top: 38px;
        padding: 22px 10px 10px;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
    }
</style>
""", unsafe_allow_html=True)


if not is_logged_in():
    hide_default_nav(hide_sidebar=True)

    st.markdown(
        """
        <style>
            .login-header h2 {
                font-size: 32px !important;
            }

            .login-header p {
                font-size: 16px;
                line-height: 1.6;
            }

            [data-testid="stTabs"] button {
                font-size: 16px;
            }

            [data-testid="stTextInput"] label {
                font-size: 16px;
            }

            [data-testid="stTextInput"] input {
                font-size: 16px;
                min-height: 46px;
            }

            [data-testid="stFormSubmitButton"] button,
            [data-testid="stButton"] button {
                font-size: 16px;
                min-height: 46px;
            }

            [data-testid="stAlert"] {
                font-size: 15px;
                line-height: 1.6;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col_center, _ = st.columns([1, 1.4, 1])

    with col_center:
        st.markdown("""
        <div class="login-header">
            <h2>🏔️ Portal Autentikasi</h2>
            <p>Sistem Clustering dan Analisis Dampak Tanah Longsor</p>
        </div>
        """, unsafe_allow_html=True)

        tab_admin, tab_guest = st.tabs([
            "🔐 Login Administrator",
            "🌐 Akses Tamu (Guest)",
        ])

        with tab_admin:
            st.markdown("<br>", unsafe_allow_html=True)

            with st.form("admin_secure_login_form"):
                username_input = st.text_input(
                    "Username",
                    placeholder="Masukkan username admin...",
                )

                password_input = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Masukkan password...",
                )

                submit = st.form_submit_button(
                    "Masuk ke Sistem",
                    use_container_width=True,
                )

                if submit:
                    if not username_input or not password_input:
                        st.warning("Harap isi username dan password.")
                    elif check_admin_login(
                        username_input,
                        password_input,
                    ):
                        login_user(username_input, "admin")
                        st.rerun()
                    else:
                        st.error("Username atau password salah.")

        with tab_guest:
            st.markdown("<br>", unsafe_allow_html=True)

            st.info(
                "Sebagai Guest, Anda dapat melihat data dan hasil "
                "clustering, tetapi tidak dapat mengunggah atau mengubah data."
            )

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button(
                "Masuk sebagai Guest",
                use_container_width=True,
                type="secondary",
            ):
                login_user("Guest", "guest")
                st.rerun()

    st.stop()


show_sidebar(active_page="Home")

username = st.session_state.username
user_type = st.session_state.user_type

st.markdown(f"Selamat datang, **{username}!**")
if user_type == "guest":
    st.info(
        "Anda masuk sebagai Guest. Anda dapat melihat data dan hasil "
        "analisis, tetapi tidak dapat mengunggah atau mengubah data."
    )
else:
    st.success(
        "Anda masuk sebagai Admin. Anda dapat mengelola data dan "
        "menjalankan clustering."
    )

st.markdown("""
<div class="home-hero">
    <div class="home-eyebrow">Dashboard Penelitian</div>
    <div class="home-title">
        ⛰️ Sistem Clustering Wilayah Berdasarkan Dampak Tanah Longsor
    </div>
    <div class="home-description">
        Aplikasi ini dikembangkan untuk mengelompokkan wilayah kabupaten/kota
        di Indonesia berdasarkan karakteristik dampak tanah longsor
        menggunakan algoritma K-Medoids dan OPTICS. Melalui pengolahan data,
        evaluasi clustering, dan visualisasi, pengguna dapat mempelajari
        persamaan serta perbedaan karakteristik dampak tanah longsor antarwilayah.
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "images/Tanah Longsor.jpeg",
        caption="Dampak tanah longsor terhadap permukiman warga.",
        use_container_width=True,
    )

st.divider()

st.markdown("""
  #### 📊 Fitur Utama
""")

col_feature1, col_feature2 = st.columns(2)

with col_feature1:
    st.markdown("""
    **Untuk Administrator:**
    - ✅ Upload dan import data longosr
    - ✅ Melakukan proses clustering dengan berbagai parameter
    - ✅ Normalisasi dan preprocessing data
    - ✅ Visualisasi hasil clustering 2D dan 3D
    - ✅ Evaluasi performa clustering
    - ✅ Export hasil clustering
    - ✅ Manajemen data dan pengguna
    """)

with col_feature2:
    st.markdown("""
    **Untuk Guest:**
    - 👁️ Melihat hasil clustering yang tersedia
    - 👁️ Mengakses visualisasi data
    - 👁️ Membaca laporan analisis
    - 👁️ Download hasil clustering
    
    *Note: Guest tidak dapat mengubah atau menambah data*
    """)

st.markdown("""
    #### 🎯 Tujuan Aplikasi
    - Mengelompokkan wilayah kabupaten/kota berdasarkan karakteristik dampak tanah longsor.
    - Mengidentifikasi persamaan dan perbedaan karakteristik dampak tanah longsor antarwilayah.
    - Menganalisis karakteristik setiap cluster berdasarkan variabel dampak yang digunakan.
    - Menyediakan visualisasi hasil clustering dalam bentuk tabel, grafik, dan peta yang mudah dipahami.

    #### 🔧 Teknologi yang Digunakan
    - **K-Medoids**: Algoritma clustering berbasis partisi untuk mengelompokkan wilayah berdasarkan kemiripan karakteristik dampak tanah longsor.
    - **OPTICS**: Algoritma clustering berbasis kepadatan untuk mengidentifikasi struktur cluster berdasarkan kepadatan data.
    - **Min-Max Scaler**: Normalisasi data agar variabel memiliki rentang nilai yang sebanding.
    - **Silhouette Score**: Evaluasi kualitas clustering berdasarkan kekompakan cluster dan pemisahan antarkelompok.
    - **Pandas dan NumPy**: Pengolahan dan manipulasi data penelitian.
    - **Neon (PostgreSQL)**: Basis data untuk penyimpanan informasi aplikasi.
    - **Streamlit**: Framework untuk membangun antarmuka aplikasi web.
""")

st.markdown("""
    <div class="home-footer">
        © 2026 Alvin Kurniawan
        <br>
        Teknik Informatika · Universitas Tarumanagara
    </div>
""", unsafe_allow_html=True)