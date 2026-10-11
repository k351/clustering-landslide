
import streamlit as st

from components.auth import require_login
from components.sidebar import show_sidebar

st.set_page_config(
    page_title="Tentang",
    page_icon="📊",
    layout="wide"
)

require_login()
show_sidebar()

st.markdown("""
<style>
    .about-hero {
        text-align: center;
        padding: 42px 24px;
        margin-bottom: 28px;
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            rgba(59, 130, 246, 0.13),
            rgba(16, 185, 129, 0.09)
        );
        border: 1px solid rgba(128, 128, 128, 0.22);
    }

    .about-eyebrow {
        display: inline-block;
        padding: 6px 12px;
        margin-bottom: 15px;
        border-radius: 20px;
        background: rgba(59, 130, 246, 0.12);
        color: #3B82F6;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    .about-title {
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 14px;
        overflow-wrap: anywhere;
    }

    .about-subtitle {
        max-width: 780px;
        margin: 0 auto;
        font-size: 16px;
        line-height: 1.8;
        opacity: 0.8;
    }

    .section-title {
        font-size: 1.4rem;
        font-weight: 750;
        margin: 24px 0 16px;
    }

    .description {
        font-size: 15px;
        line-height: 1.9;
        text-align: justify;
    }

    .description p {
        margin-bottom: 14px;
    }

    .advisor-card {
        box-sizing: border-box;
        height: 100%;
        min-height: 190px;
        padding: 26px 20px;
        border-radius: 16px;
        text-align: center;
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.2);
        transition: border-color 0.2s ease,
                    transform 0.2s ease;
    }

    .advisor-card:hover {
        border-color: rgba(59, 130, 246, 0.55);
        transform: translateY(-2px);
    }

    .advisor-icon {
        font-size: 30px;
        margin-bottom: 14px;
    }

    .advisor-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        opacity: 0.65;
        margin-bottom: 12px;
    }

    .advisor-name {
        font-size: 16px;
        font-weight: 750;
        line-height: 1.6;
        margin-bottom: 8px;
        overflow-wrap: anywhere;
    }

    .advisor-university {
        font-size: 13px;
        opacity: 0.7;
    }

    .info-card {
        box-sizing: border-box;
        width: 100%;
        padding: 22px;
        margin-bottom: 14px;
        border-radius: 15px;
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    .info-label,
    .profile-label {
        font-size: 11px;
        font-weight: 750;
        letter-spacing: 1.1px;
        text-transform: uppercase;
        opacity: 0.65;
        margin-bottom: 9px;
    }

    .info-value,
    .profile-value {
        font-size: 15px;
        font-weight: 600;
        line-height: 1.75;
        overflow-wrap: anywhere;
    }

    .profile-card {
        box-sizing: border-box;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 24px;
        width: 100%;
        padding: 24px;
        margin-bottom: 14px;
        border-radius: 16px;
        background: rgba(128, 128, 128, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.2);
    }

    .profile-item {
        flex: 1 1 180px;
        min-width: 0;
    }

    .tech-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .tech-item {
        display: inline-block;
        padding: 7px 11px;
        border-radius: 9px;
        background: rgba(59, 130, 246, 0.09);
        border: 1px solid rgba(59, 130, 246, 0.22);
        font-size: 12px;
        font-weight: 650;
        line-height: 1.4;
    }

    .footer {
        text-align: center;
        opacity: 0.6;
        font-size: 13px;
        line-height: 1.8;
        margin-top: 38px;
        padding: 22px 10px 10px;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
    }

    @media (max-width: 768px) {
        .about-hero {
            padding: 30px 18px;
        }

        .about-title {
            font-size: 1.8rem;
        }

        .about-subtitle {
            font-size: 14px;
        }

        .description {
            font-size: 14px;
        }

        .profile-card {
            gap: 18px;
            padding: 20px;
        }

        .profile-item {
            flex-basis: 100%;
        }
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="about-hero">
    <div class="about-eyebrow">Informasi Perancangan</div>
    <div class="about-title">Tentang Website Ini</div>
    <div class="about-subtitle">
        Platform analisis dan pengelompokan wilayah berdasarkan
        karakteristik dampak tanah longsor di Indonesia menggunakan
        algoritma K-Medoids dan OPTICS.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">🎯 Latar Belakang Perancangan</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="description">
    <p>
        Website ini dirancang sebagai platform untuk melakukan
        pengelompokan wilayah berdasarkan karakteristik dampak
        tanah longsor di Indonesia menggunakan algoritma
        <strong>K-Medoids</strong> dan <strong>OPTICS</strong>.
    </p>
    <p>
        Data kejadian dan dampak bencana digunakan untuk
        mengidentifikasi kesamaan karakteristik dampak antarwilayah.
        Hasil pengelompokan disajikan sebagai bahan analisis untuk
        memahami variasi dampak tanah longsor di berbagai wilayah.
    </p>
    <p>
        Melalui tabel, visualisasi, dan peta, website ini membantu
        pengguna mengeksplorasi hasil pengelompokan serta memahami
        karakteristik setiap kelompok wilayah.
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown(
    '<div class="section-title">👤 Profil Perancang</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="profile-card">
    <div class="profile-item">
        <div class="profile-label">Nama</div>
        <div class="profile-value">Alvin Kurniawan</div>
    </div>
    <div class="profile-item">
        <div class="profile-label">Program Studi</div>
        <div class="profile-value">Teknik Informatika</div>
    </div>
    <div class="profile-item">
        <div class="profile-label">Angkatan</div>
        <div class="profile-value">2023</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown(
    '<div class="section-title">👨‍🏫 Dosen Pembimbing</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("""
    <div class="advisor-card">
        <div class="advisor-icon">🎓</div>
        <div class="advisor-title">Pembimbing Utama</div>
        <div class="advisor-name">
            Lely Hiryanto, ST., M.Sc., PhD.
        </div>
        <div class="advisor-university">
            Universitas Tarumanagara
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="advisor-card">
        <div class="advisor-icon">🎓</div>
        <div class="advisor-title">Pembimbing Pendamping</div>
        <div class="advisor-name">
            Nama Pembimbing Pendamping
        </div>
        <div class="advisor-university">
            Universitas Tarumanagara
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.markdown(
    '<div class="section-title">⚙️ Informasi Teknis</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="info-card">
    <div class="info-label">Algoritma Clustering</div>
    <div class="tech-list">
        <span class="tech-item">K-Medoids</span>
        <span class="tech-item">OPTICS</span>
    </div>
</div>

<div class="info-card">
    <div class="info-label">Sumber Data</div>
    <div class="info-value">
        Data kejadian dan dampak bencana tanah longsor dari BNPB.
    </div>
</div>

<div class="info-card">
    <div class="info-label">Teknologi yang Digunakan</div>
    <div class="tech-list">
        <span class="tech-item">Python</span>
        <span class="tech-item">Streamlit</span>
        <span class="tech-item">PostgreSQL</span>
        <span class="tech-item">Scikit-learn</span>
        <span class="tech-item">Pandas</span>
        <span class="tech-item">GeoPandas</span>
        <span class="tech-item">Folium</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    © 2026 Alvin Kurniawan
    <br>
    Teknik Informatika · Universitas Tarumanagara
</div>
""", unsafe_allow_html=True)