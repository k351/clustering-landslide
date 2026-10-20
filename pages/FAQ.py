import streamlit as st

from components.auth import require_login
from components.sidebar import show_sidebar


st.set_page_config(
    page_title="FAQ",
    page_icon=":material/help_outline:",
    layout="wide",
)

require_login()
show_sidebar(active_page="FAQ")

FAQ_ITEMS = [
    {
        "category": "Tentang penelitian",
        "question": "Apa tujuan dari website ini?",
        "answer": (
            "Website ini dikembangkan sebagai bagian dari penelitian tugas "
            "akhir untuk mengelompokkan wilayah kabupaten/kota di Indonesia "
            "berdasarkan karakteristik dampak tanah longsor. Hasilnya membantu "
            "pengguna memahami persamaan dan perbedaan dampak antarwilayah "
            "sebagai bahan pertimbangan dalam analisis dan penentuan prioritas "
            "mitigasi bencana."
        ),
    },
    {
        "category": "Tentang penelitian",
        "question": "Data apa saja yang digunakan?",
        "answer": (
            "Data utama bersumber dari Data dan Informasi Bencana Indonesia "
            "(DIBI) yang dikelola oleh BNPB, dengan rentang 1 Januari 2014 "
            "sampai 31 Desember 2025. Variabel menggambarkan dampak tanah "
            "longsor, seperti jumlah korban meninggal, hilang, luka-luka, "
            "mengungsi, serta kerusakan rumah dan fasilitas umum. Data "
            "diagregasikan pada tingkat kabupaten/kota sesuai kebutuhan analisis."
        ),
    },
    {
        "category": "Tentang penelitian",
        "question": "Apa yang dimaksud dengan clustering?",
        "answer": (
            "Clustering adalah teknik unsupervised learning untuk "
            "mengelompokkan data berdasarkan kemiripan karakteristiknya. "
            "Dalam penelitian ini, teknik tersebut digunakan untuk mencari "
            "wilayah dengan pola dampak tanah longsor yang serupa, tanpa "
            "label kelompok yang ditentukan sebelumnya."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Algoritma apa yang digunakan?",
        "answer": (
            "Website ini menerapkan K-Medoids dan OPTICS. K-Medoids membentuk "
            "sejumlah cluster dengan medoid sebagai objek perwakilan. OPTICS "
            "menganalisis struktur kepadatan untuk menemukan kelompok dengan "
            "kepadatan berbeda dan menandai data yang tidak tergabung sebagai "
            "noise."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Bagaimana tahapan clustering dilakukan?",
        "answer": (
            "Secara umum, analisis dimulai dari pengumpulan data, pemeriksaan "
            "dan preprocessing, agregasi berdasarkan kabupaten/kota, "
            "normalisasi dengan Min-Max Scaling, penerapan algoritma, "
            "evaluasi hasil, lalu profiling dan visualisasi cluster melalui "
            "ringkasan statistik, grafik, tabel, dan peta."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Apa perbedaan K-Medoids dan OPTICS?",
        "answer": (
            "K-Medoids memerlukan jumlah cluster yang ditentukan sebagai "
            "parameter dan menggunakan medoid sebagai perwakilan cluster. "
            "OPTICS menganalisis struktur kepadatan untuk menemukan kelompok "
            "tanpa menentukan jumlah cluster secara langsung di awal. "
            "OPTICS juga dapat menandai wilayah yang tidak masuk cluster "
            "sebagai noise."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Bagaimana kualitas hasil clustering dinilai?",
        "answer": (
            "Kualitas dapat ditinjau menggunakan metrik evaluasi internal. "
            "Silhouette Score membandingkan kedekatan data dengan cluster "
            "sendiri dan cluster lain; nilai yang lebih tinggi umumnya lebih "
            "baik. Davies-Bouldin Index (DBI) membandingkan kemiripan dalam "
            "cluster dengan pemisahan antarkluster; nilai yang lebih rendah "
            "umumnya lebih baik. Interpretasinya tetap perlu mempertimbangkan "
            "algoritma dan struktur data."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Apakah hasil clustering menunjukkan penyebab tanah longsor?",
        "answer": (
            "Tidak. Penelitian ini mengelompokkan wilayah berdasarkan "
            "karakteristik dampak, bukan mengidentifikasi hubungan sebab-akibat "
            "atau faktor penyebab tanah longsor. Cluster menunjukkan kemiripan "
            "pola pada variabel yang dianalisis, bukan bukti bahwa suatu "
            "variabel menyebabkan dampak tertentu."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Apa manfaat hasil clustering bagi mitigasi bencana?",
        "answer": (
            "Hasilnya memberi gambaran wilayah dengan karakteristik dampak "
            "serupa dan dapat menjadi bahan pertimbangan awal untuk analisis "
            "lebih lanjut, penentuan prioritas kajian, serta perencanaan "
            "mitigasi dan kesiapsiagaan. Hasil clustering bukan penetapan "
            "tingkat risiko resmi dan tidak secara langsung menentukan "
            "kebijakan."
        ),
    },
    {
        "category": "Metode analisis",
        "question": "Apakah hasil clustering dapat dijadikan keputusan final?",
        "answer": (
            "Tidak. Hasil clustering merupakan informasi pendukung untuk "
            "eksplorasi dan analisis data. Hasilnya dapat dipertimbangkan "
            "sebagai langkah awal, tetapi tidak menggantikan kajian risiko "
            "bencana, verifikasi kondisi lapangan, atau keputusan instansi "
            "yang berwenang."
        ),
    },
    {
        "category": "Penggunaan aplikasi",
        "question": "Bagaimana cara menggunakan website ini?",
        "answer": (
            "Buka halaman Data untuk melihat dataset, kemudian buka halaman "
            "Clustering untuk memilih algoritma dan parameter yang tersedia. "
            "Jalankan proses clustering, lalu tinjau ringkasan cluster, "
            "statistik, grafik, tabel, dan visualisasi wilayah yang tersedia."
        ),
    },
    {
        "category": "Penggunaan aplikasi",
        "question": "Bagaimana cara menghubungi pengembang jika menemukan masalah?",
        "answer": (
            "Jika menemukan kendala penggunaan, kesalahan tampilan, atau hasil "
            "yang tidak sesuai, hubungi pengembang melalui kontak yang "
            "disediakan oleh pengelola aplikasi."
        ),
    },
]

st.markdown(
    """
    <style>
        .faq-intro {
            border-left: 4px solid #68836f;
            padding: 4px 0 4px 18px;
            margin: 10px 0 24px;
        }

        .faq-kicker {
            color: #68836f;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .faq-description {
            max-width: 760px;
            line-height: 1.7;
            opacity: 0.75;
        }

        [data-testid="stExpander"] {
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="faq-intro">
        <div class="faq-kicker">Panduan aplikasi</div>
        <h1>Pertanyaan yang sering ditanyakan</h1>
        <div class="faq-description">
            Informasi tentang data, metode analisis, dan penggunaan sistem
            clustering dampak tanah longsor.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

categories = ["Semua topik", "Tentang penelitian", "Metode analisis", "Penggunaan aplikasi"]
selected_category = st.segmented_control(
    "Pilih topik FAQ",
    options=categories,
    default="Semua topik",
    label_visibility="collapsed",
)
search_query = st.text_input(
    "Cari pertanyaan",
    placeholder="Contoh: K-Medoids, data, hasil clustering",
    icon=":material/search:",
)

visible_items = [
    item
    for item in FAQ_ITEMS
    if (
        selected_category == "Semua topik"
        or item["category"] == selected_category
    )
    and (
        not search_query
        or search_query.casefold() in item["question"].casefold()
        or search_query.casefold() in item["answer"].casefold()
        or search_query.casefold() in item["category"].casefold()
    )
]

st.caption(f"{len(visible_items)} pertanyaan")

if not visible_items:
    st.info("Tidak ada pertanyaan yang cocok. Coba kata kunci lain.")
else:
    previous_category = None
    for item in visible_items:
        if selected_category == "Semua topik" and item["category"] != previous_category:
            st.subheader(item["category"])
            previous_category = item["category"]

        with st.expander(item["question"]):
            st.write(item["answer"])

st.markdown(
    """
    <div style="
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        color: rgba(128, 128, 128, 0.85);
        font-size: 13px;
        line-height: 1.8;
        margin-top: 36px;
        padding-top: 18px;
        text-align: center;
    ">
        © 2026 Alvin Kurniawan<br>
        Teknik Informatika · Universitas Tarumanagara
    </div>
    """,
    unsafe_allow_html=True,
)