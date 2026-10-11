import streamlit as st

from components.auth import require_login
from components.sidebar import show_sidebar


st.set_page_config(
    page_title="FAQ",
    page_icon="🔍",
    layout="wide",
)

require_login()
show_sidebar(active_page="FAQ")

def show_footer():
    st.markdown("""
    <style>
        .footer {
            text-align: center;
            opacity: 0.6;
            font-size: 13px;
            line-height: 1.8;
            margin-top: 38px;
            padding: 22px 10px 10px;
            border-top: 1px solid rgba(128, 128, 128, 0.2);
        }
    </style>

    <div class="footer">
        © 2026 Alvin Kurniawan
        <br>
        Teknik Informatika · Universitas Tarumanagara
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    """
    <h1 style="text-align: center;">
        FREQUENTLY ASKED QUESTIONS
    </h1>
    <p style="
        text-align: center;
        color: #9CA3AF;
        margin-bottom: 2rem;
    ">
        Pertanyaan umum mengenai aplikasi clustering dampak tanah longsor
    </p>
    """,
    unsafe_allow_html=True,
)

with st.expander("Apa tujuan dari website ini?"):
    st.write(
        """
        Website ini dikembangkan sebagai bagian dari penelitian tugas akhir
        untuk mengelompokkan wilayah kabupaten/kota di Indonesia berdasarkan
        karakteristik dampak tanah longsor. Hasil pengelompokan diharapkan
        dapat membantu pengguna memahami persamaan dan perbedaan dampak
        tanah longsor antarwilayah sebagai bahan pertimbangan dalam analisis
        dan penentuan prioritas mitigasi bencana.
        """
    )

with st.expander("Data apa saja yang digunakan dalam website ini?"):
    st.write(
        """
        Data utama yang digunakan bersumber dari Data dan Informasi Bencana
        Indonesia (DIBI) yang dikelola oleh Badan Nasional Penanggulangan
        Bencana (BNPB), dengan rentang periode 1 Januari 2014 sampai
        31 Desember 2025.

        Variabel yang digunakan menggambarkan karakteristik dampak tanah
        longsor, antara lain jumlah korban meninggal, hilang, luka-luka,
        dan mengungsi, serta kerusakan rumah dan fasilitas umum. 

        Data diproses dan diagregasikan pada tingkat kabupaten/kota
        sesuai kebutuhan analisis.
        """
    )

with st.expander("Apa yang dimaksud dengan clustering?"):
    st.write(
        """
        Clustering merupakan teknik unsupervised learning yang digunakan
        untuk mengelompokkan data berdasarkan kemiripan karakteristiknya.
        Dalam penelitian ini, clustering digunakan untuk mengidentifikasi
        kelompok wilayah yang memiliki pola karakteristik dampak tanah
        longsor yang serupa tanpa menggunakan label kelas yang telah
        ditentukan sebelumnya.
        """
    )


with st.expander("Algoritma apa yang digunakan dalam website ini?"):
    st.write(
        """
        Website ini menerapkan dua algoritma clustering, yaitu K-Medoids
        dan OPTICS.

        - **K-Medoids:** membentuk sejumlah cluster berdasarkan medoid,
          yaitu objek data yang mewakili suatu cluster.
        - **OPTICS:** mengidentifikasi struktur kepadatan data untuk
          membantu menemukan kelompok dengan kepadatan yang berbeda
          serta mengidentifikasi data yang tidak tergabung dalam cluster
          tertentu.

        Kedua algoritma digunakan untuk menganalisis pola pengelompokan
        wilayah berdasarkan karakteristik dampak tanah longsor.
        """
    )


with st.expander("Bagaimana tahapan clustering dilakukan?"):
    st.markdown(
        """
        Secara umum, tahapan analisis dalam penelitian ini meliputi:

        1. **Pengumpulan data:** memperoleh data kejadian dan dampak tanah
           longsor dari sumber data yang digunakan dalam penelitian.
        2. **Preprocessing:** memeriksa kelengkapan data, menangani data
           yang tidak sesuai, dan menyiapkan variabel analisis.
        3. **Agregasi wilayah:** menggabungkan data berdasarkan wilayah
           kabupaten/kota sesuai periode penelitian.
        4. **Normalisasi:** menyetarakan skala variabel menggunakan
           Min-Max Scaling.
        5. **Clustering:** menerapkan algoritma K-Medoids dan OPTICS.
        6. **Evaluasi:** mengevaluasi kualitas hasil clustering menggunakan
           metrik yang sesuai, seperti Silhouette Score, Davies-Bouldin
           Index, dan Calinski-Harabasz Index apabila tersedia.
        7. **Profiling dan visualisasi:** menampilkan karakteristik setiap
           cluster melalui ringkasan statistik, grafik, tabel, dan peta.
        """
    )

with st.expander("Apa perbedaan K-Medoids dan OPTICS?"):
    st.write(
        """
        K-Medoids memerlukan jumlah cluster yang ditentukan sebagai
        parameter, sedangkan OPTICS menganalisis struktur kepadatan data
        untuk menemukan pola kelompok tanpa harus menentukan jumlah
        cluster secara langsung di awal.

        K-Medoids menggunakan medoid sebagai pusat representatif cluster.
        OPTICS menghasilkan informasi urutan dan keterjangkauan kepadatan
        yang dapat digunakan untuk mengidentifikasi struktur cluster
        serta data noise. Hasil kedua algoritma dapat dibandingkan untuk
        memahami karakteristik pengelompokan wilayah.
        """
    )

with st.expander("Bagaimana cara menentukan kualitas hasil clustering?"):
    st.write(
        """
        Kualitas hasil clustering dapat dianalisis menggunakan metrik
        evaluasi internal.

        - **Silhouette Score:** mengukur seberapa dekat suatu data dengan
          cluster-nya dibandingkan cluster lain. Nilai yang lebih tinggi
          umumnya menunjukkan pemisahan cluster yang lebih baik.
        - **Davies-Bouldin Index (DBI):** mengukur kemiripan dalam cluster
          dibandingkan pemisahan antarkluster. Nilai yang lebih rendah
          umumnya lebih baik.

        Interpretasi evaluasi perlu mempertimbangkan karakteristik
        algoritma dan struktur data yang dianalisis.
        """
    )


with st.expander("Apa manfaat hasil clustering bagi mitigasi bencana?"):
    st.write(
        """
        Hasil clustering dapat membantu memberikan gambaran mengenai
        wilayah-wilayah yang memiliki karakteristik dampak tanah longsor
        serupa. Informasi tersebut dapat menjadi bahan pertimbangan awal
        untuk analisis lebih lanjut, penentuan prioritas kajian, serta
        perencanaan mitigasi dan kesiapsiagaan bencana.

        Hasil clustering bukan penetapan tingkat risiko resmi dan tidak
        secara langsung menentukan kebijakan. Keputusan penanganan bencana
        tetap perlu mempertimbangkan informasi tambahan, kondisi lokal,
        serta penilaian dari pihak berwenang.
        """
    )

with st.expander("Bagaimana cara menggunakan website ini?"):
    st.markdown(
        """
        Secara umum, pengguna dapat mengikuti langkah-langkah berikut:

        1. Login untuk mengakses fitur aplikasi.
        2. Buka halaman **Data** untuk melihat dataset yang tersedia.
        3. Buka halaman **Clustering** untuk memilih algoritma dan
           parameter analisis yang disediakan.
        4. Jalankan proses clustering sesuai pilihan.
        5. Buka halaman hasil atau profil clustering untuk melihat
           ringkasan cluster, statistik, grafik, dan visualisasi wilayah
           yang tersedia.
        6. Gunakan hasil tersebut untuk memahami karakteristik dampak
           tanah longsor pada kelompok wilayah yang terbentuk.
        """
    )


with st.expander("Apakah hasil clustering menunjukkan penyebab tanah longsor?"):
    st.write(
        """
        Tidak. Penelitian ini berfokus pada pengelompokan wilayah berdasarkan
        karakteristik dampak tanah longsor, bukan untuk mengidentifikasi
        hubungan sebab-akibat atau menentukan faktor penyebab tanah longsor.

        Cluster yang terbentuk menunjukkan kemiripan pola pada variabel
        yang digunakan dalam analisis, bukan bukti bahwa suatu variabel
        menyebabkan dampak tertentu.
        """
    )

with st.expander("Apakah hasil clustering dapat dijadikan keputusan final?"):
    st.write(
        """
        Tidak. Hasil clustering merupakan informasi pendukung untuk
        eksplorasi dan analisis data. Hasilnya dapat digunakan sebagai
        bahan pertimbangan awal, tetapi tidak menggantikan kajian risiko
        bencana, verifikasi kondisi lapangan, maupun keputusan dari
        instansi yang berwenang.
        """
    )

with st.expander("Bagaimana cara menghubungi pengembang jika menemukan masalah?"):
    st.write(
        """
        Jika menemukan kendala penggunaan, kesalahan tampilan, atau hasil
        yang tidak sesuai, pengguna dapat menghubungi pengembang melalui
        kontak yang disediakan oleh pengelola aplikasi.
        """
    )

show_footer()