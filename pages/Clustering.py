from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from components.auth import is_logged_in, require_login
from components.dataset_store import load_active_dataset
from components.sidebar import show_sidebar


st.set_page_config(
    page_title="Clustering Dampak Longsor",
    page_icon="🧭",
    layout="wide",
)

APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
GEOJSON_PATH = DATA_DIR / "Indonesia_cities.geojson"

FEATURE_LABELS = [
    "Jumlah Korban Meninggal",
    "Jiwa Terdampak",
    "Total Rumah Rusak",
    "Total Fasilitas Umum Rusak",
]
CLUSTER_PALETTE = (
    "#0f766e",
    "#2563eb",
    "#d97706",
    "#9333ea",
    "#db2777",
    "#0891b2",
    "#65a30d",
    "#ea580c",
    "#4f46e5",
    "#059669",
    "#be123c",
    "#a16207",
)

st.markdown(
    """
    <style>
        .cluster-hero {
            padding: 1.7rem 1.9rem;
            border: 1px solid rgba(20, 184, 166, 0.25);
            border-radius: 20px;
            background:
                radial-gradient(ellipse at top right, rgba(20, 184, 166, .18), transparent 42%),
                linear-gradient(135deg, rgba(15, 23, 42, .96), rgba(17, 54, 54, .88));
            margin: .4rem 0 1.25rem;
        }
        .cluster-eyebrow {
            color: #5eead4;
            font-size: .76rem;
            font-weight: 750;
            letter-spacing: .14em;
            text-transform: uppercase;
            margin-bottom: .45rem;
        }
        .cluster-hero h1 {
            color: #f8fafc;
            font-size: clamp(1.8rem, 3vw, 2.55rem);
            line-height: 1.15;
            margin: 0 0 .65rem;
        }
        .cluster-hero p {
            color: #cbd5e1;
            font-size: 1rem;
            line-height: 1.7;
            max-width: 820px;
            margin: 0;
        }
        .section-kicker {
            color: #0f766e;
            font-size: .75rem;
            font-weight: 750;
            letter-spacing: .12em;
            text-transform: uppercase;
        }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, .2);
            border-radius: 14px;
            padding: .85rem 1rem;
            background: rgba(128, 128, 128, .035);
        }
        .cluster-note {
            border-left: 3px solid #14b8a6;
            padding: .45rem .8rem;
            color: #64748b;
            font-size: .9rem;
            line-height: 1.6;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def _normalized_column_name(value: object) -> str:
    """Normalisasi nama kolom agar variasi huruf dan tanda baca bisa dicocokkan."""
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _find_column(columns: pd.Index, aliases: tuple[str, ...]) -> str | None:
    """Cari nama kolom yang cocok dengan salah satu alias secara tidak peka format.

    Args:
        columns: Daftar nama kolom pada dataset.
        aliases: Nama kolom alternatif yang dapat diterima.

    Returns:
        Nama kolom asli yang cocok, atau ``None`` jika tidak ditemukan.
    """
    normalized = {_normalized_column_name(column): str(column) for column in columns}
    for alias in aliases:
        match = normalized.get(_normalized_column_name(alias))
        if match is not None:
            return match
    return None


def _region_code_key(value: object) -> str | None:
    """Ubah kode wilayah menjadi kunci digit empat karakter untuk pencocokan peta.

    Nilai kosong atau tanpa digit akan menghasilkan ``None``.
    """
    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        numeric_value = float(text)
    except ValueError:
        numeric_value = None

    if numeric_value is not None and np.isfinite(numeric_value):
        if abs(numeric_value) < 100:
            text = f"{numeric_value:.2f}"
        elif numeric_value.is_integer():
            text = str(int(numeric_value))

    digits = re.sub(r"\D", "", text)
    return digits.zfill(4) if digits else None


def _display_region_code(code_key: str) -> str:
    """Format kunci kode wilayah empat digit dengan titik pemisah."""
    if len(code_key) == 4:
        return f"{code_key[:2]}.{code_key[2:]}"
    return code_key


def _cluster_color(label: str) -> str:
    """Pilih warna peta untuk label cluster atau label noise."""
    if label == "Noise":
        return "#64748b"
    cluster_number = int(label.rsplit(" ", 1)[-1])
    return CLUSTER_PALETTE[(cluster_number - 1) % len(CLUSTER_PALETTE)]


def _resolve_impact_columns(columns: pd.Index) -> dict[str, list[str]]:
    """Temukan kolom dampak yang diperlukan dan kelompokkan menurut jenis fitur.

    Args:
        columns: Daftar nama kolom pada dataset.

    Returns:
        Kolom sumber untuk korban meninggal, warga terdampak, kerusakan rumah,
        dan kerusakan fasilitas umum.

    Raises:
        ValueError: Jika satu atau lebih kelompok kolom wajib tidak ditemukan.
    """
    fatalities = _find_column(columns, ("Meninggal",))
    missing = []
    if fatalities is None:
        missing.append("Meninggal")

    menderita = _find_column(columns, ("Menderita",))
    mengungsi = _find_column(columns, ("Mengungsi",))
    if menderita is not None and mengungsi is not None:
        affected_people = [menderita, mengungsi]
    else:
        combined = _find_column(
            columns,
            (
                "menderita_mengungsi",
                "Menderita Mengungsi",
                "Menderita dan Mengungsi",
            ),
        )
        if combined is not None:
            affected_people = [combined]
        else:
            affected_people = []
            missing.append("Menderita dan Mengungsi (atau kolom gabungan)")

    injury = _find_column(columns, ("Luka dan Sakit", "Luka / Sakit"))
    if injury is None:
        missing.append("Luka dan Sakit")

    missing_person = _find_column(columns, ("Hilang",))
    if missing_person is None:
        missing.append("Hilang")

    house_damage = [
        _find_column(columns, ("Rumah Rusak Berat",)),
        _find_column(columns, ("Rumah Rusak Sedang",)),
        _find_column(columns, ("Rumah Rusak Ringan",)),
    ]
    if any(column is None for column in house_damage):
        missing.append("Rumah Rusak Berat, Rumah Rusak Sedang, dan Rumah Rusak Ringan")

    public_facilities = [
        _find_column(columns, ("Satuan Pendidikan Rusak",)),
        _find_column(columns, ("Rumah Ibadat Rusak",)),
        _find_column(columns, ("Fasilitas Pelayanan Kesehatan Rusak",)),
        _find_column(columns, ("Kantor Rusak",)),
        _find_column(columns, ("Jembatan Rusak",)),
    ]
    if any(column is None for column in public_facilities):
        missing.append(
            "Satuan Pendidikan Rusak, Rumah Ibadat Rusak, "
            "Fasilitas Pelayanan Kesehatan Rusak, Kantor Rusak, dan Jembatan Rusak"
        )

    if missing:
        raise ValueError("Kolom wajib tidak ditemukan: " + "; ".join(missing) + ".")

    return {
        "fatalities": [fatalities],
        "affected_people": affected_people + [injury, missing_person],
        "house_damage": [column for column in house_damage if column is not None],
        "facility_damage": [
            column for column in public_facilities if column is not None
        ],
    }


def prepare_regional_data(
    dataset: pd.DataFrame,
    selected_year: int | None,
) -> tuple[pd.DataFrame, int, int]:
    """Siapkan dan agregasikan fitur dampak longsor untuk setiap kabupaten.

    Data dapat difilter berdasarkan tahun. Baris dengan informasi wilayah atau
    nilai fitur yang tidak valid dihapus sebelum jumlah dampak dijumlahkan.

    Args:
        dataset: Data kejadian longsor yang memuat kolom wilayah, tahun, dan dampak.
        selected_year: Tahun yang dipilih, atau ``None`` untuk semua tahun.

    Returns:
        Tuple berisi data fitur per kabupaten, jumlah baris yang dihapus, dan
        jumlah baris valid yang digunakan.

    Raises:
        ValueError: Jika kolom wajib tidak tersedia atau tidak ada baris valid.
    """
    code_column = _find_column(dataset.columns, ("Kode Kabupaten",))
    name_column = _find_column(dataset.columns, ("Kabupaten",))
    year_column = _find_column(dataset.columns, ("Tahun",))
    if code_column is None or name_column is None or year_column is None:
        raise ValueError(
            "Dataset wajib memiliki kolom Kode Kabupaten, Kabupaten, dan Tahun."
        )

    impact_columns = _resolve_impact_columns(dataset.columns)
    source_columns = list(
        dict.fromkeys(
            column
            for group in impact_columns.values()
            for column in group
        )
    )
    work = dataset[[code_column, name_column, year_column, *source_columns]].copy()
    work["_year"] = pd.to_numeric(work[year_column], errors="coerce")
    work["_region_code_key"] = work[code_column].map(_region_code_key)
    work["_region_name"] = work[name_column].astype("string").str.strip()

    if selected_year is not None:
        work = work.loc[work["_year"].eq(selected_year)].copy()

    for column in source_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work[source_columns] = work[source_columns].replace([np.inf, -np.inf], np.nan)

    required_columns = [
        "_year",
        "_region_code_key",
        "_region_name",
        *source_columns,
    ]
    before_drop = len(work)
    work = work.dropna(subset=required_columns)
    work = work.loc[work["_region_name"].ne("")].copy()
    dropped_rows = before_drop - len(work)
    if work.empty:
        raise ValueError(
            "Tidak ada baris valid untuk rentang tahun yang dipilih setelah "
            "baris dengan missing value pada fitur clustering dihapus."
        )

    work[FEATURE_LABELS[0]] = work[impact_columns["fatalities"]].sum(axis=1)
    work[FEATURE_LABELS[1]] = work[impact_columns["affected_people"]].sum(axis=1)
    work[FEATURE_LABELS[2]] = work[impact_columns["house_damage"]].sum(axis=1)
    work[FEATURE_LABELS[3]] = work[impact_columns["facility_damage"]].sum(axis=1)
    work["Kode Kabupaten"] = work["_region_code_key"].map(_display_region_code)
    work["Kabupaten"] = work["_region_name"].astype(str)

    grouped = (
        work.groupby(
            ["_region_code_key", "Kode Kabupaten", "Kabupaten"],
            as_index=False,
            sort=True,
        )[FEATURE_LABELS]
        .sum()
        .rename(columns={"_region_code_key": "_kode_peta"})
    )

    return grouped, dropped_rows, len(work)


def cluster_regions(
    regions: pd.DataFrame,
    method: str,
    cluster_count: int,
    min_samples: int,
    xi: float | None,
) -> tuple[pd.DataFrame, dict[str, float | None], dict[str, str | None]]:
    """Kelompokkan wilayah dengan K-Medoids atau OPTICS dan hitung metrik evaluasi.

    Fitur dampak dinormalisasi sebelum clustering. Noise OPTICS dikecualikan dari
    perhitungan metrik evaluasi.

    Args:
        regions: Data wilayah yang telah disiapkan beserta fitur dampaknya.
        method: Metode clustering, yaitu ``"K-Medoids"`` atau ``"OPTICS"``.
        cluster_count: Jumlah cluster yang digunakan oleh K-Medoids.
        min_samples: Jumlah minimum sampel untuk metode OPTICS.
        xi: Parameter ``xi`` OPTICS, atau ``None`` untuk menggunakan nilai default.

    Returns:
        Tuple berisi hasil wilayah berlabel cluster, nilai metrik evaluasi, dan
        catatan jika metrik tidak dapat dihitung.

    Raises:
        ValueError: Jika jumlah cluster K-Medoids tidak lebih kecil dari jumlah
            wilayah valid.
    """
    from sklearn.metrics import (
        davies_bouldin_score,
        silhouette_score,
    )
    from sklearn.preprocessing import MinMaxScaler

    feature_data = regions[FEATURE_LABELS].to_numpy(dtype=float)
    scaled_features = MinMaxScaler().fit_transform(feature_data)

    if method == "K-Medoids":
        from sklearn_extra.cluster import KMedoids

        if cluster_count >= len(regions):
            raise ValueError(
                "Jumlah cluster k harus lebih kecil daripada jumlah wilayah valid."
            )
        model = KMedoids(n_clusters=cluster_count, random_state=42, method="pam", metric="euclidean")
        labels = model.fit_predict(scaled_features)
    else:
        from sklearn.cluster import OPTICS
 
        optics = OPTICS(
            min_samples=min_samples,
            metric="euclidean",
            # p=2,
            cluster_method="xi",
        )
        if xi is not None:
            optics.set_params(xi=xi)
        labels = optics.fit_predict(scaled_features)

    result = regions.copy()
    result["_label_number"] = labels.astype(int)
    result["Cluster"] = result["_label_number"].map(
        lambda label: "Noise" if label == -1 else f"Cluster {label + 1}"
    )

    scored = result["_label_number"].to_numpy()
    valid_for_score = scored != -1 if method == "OPTICS" else np.ones(len(scored), dtype=bool)
    score_labels = scored[valid_for_score]
    unique_labels = np.unique(score_labels)
    evaluation_scores: dict[str, float | None] = {
        "silhouette": None,
        "davies_bouldin": None,
    }
    evaluation_notes: dict[str, str | None] = {
        "silhouette": None,
        "davies_bouldin": None,
    }
    if 2 <= len(unique_labels) < len(score_labels):
        score_features = scaled_features[valid_for_score]
        evaluation_scores["silhouette"] = float(
            silhouette_score(score_features, score_labels)
        )
        evaluation_scores["davies_bouldin"] = float(
            davies_bouldin_score(score_features, score_labels)
        )
    else:
        if len(unique_labels) < 2:
            note = "Evaluasi memerlukan minimal dua cluster selain noise."
        else:
            note = (
                "Evaluasi tidak dapat dihitung jika setiap wilayah menjadi "
                "cluster tersendiri."
            )
        evaluation_notes = {name: note for name in evaluation_notes}

    return result, evaluation_scores, evaluation_notes


@st.cache_data(show_spinner=False)
def load_geojson(path: str, modified_at: float) -> dict:
    """Muat data batas wilayah GeoJSON untuk ditampilkan pada peta.

    Args:
        path: Lokasi file GeoJSON.
        modified_at: Waktu modifikasi file, digunakan sebagai bagian dari kunci cache.

    Returns:
        Isi file GeoJSON dalam bentuk dictionary.
    """
    del modified_at
    with Path(path).open(encoding="utf-8") as geojson_file:
        return json.load(geojson_file)


def render_cluster_map(result: pd.DataFrame) -> int:
    """Tampilkan peta cluster kabupaten dan kembalikan jumlah wilayah yang terpetakan.

    Pencocokan batas wilayah menggunakan kode wilayah, lalu nama wilayah yang unik
    sebagai fallback.

    Args:
        result: Hasil clustering yang memuat kode, nama, label, dan fitur dampak.

    Returns:
        Jumlah wilayah hasil clustering yang berhasil dicocokkan ke batas peta.
    """
    import folium
    from streamlit_folium import st_folium

    geojson = load_geojson(str(GEOJSON_PATH), GEOJSON_PATH.stat().st_mtime)
    result_records = result.to_dict(orient="records")
    code_counts = result["_kode_peta"].value_counts()
    result_by_code = {
        region["_kode_peta"]: region
        for region in result_records
        if code_counts[region["_kode_peta"]] == 1
    }
    mapped_geojson = json.loads(json.dumps(geojson))

    cluster_names = sorted(
        (name for name in result["Cluster"].unique() if name != "Noise"),
        key=lambda label: int(label.rsplit(" ", 1)[-1]),
    )
    color_map = {name: _cluster_color(name) for name in cluster_names}
    color_map["Noise"] = _cluster_color("Noise")

    result_by_name: dict[str, list[dict]] = {}
    for region in result_records:
        name_key = _normalized_column_name(region["Kabupaten"])
        result_by_name.setdefault(name_key, []).append(region)

    boundary_names: dict[str, int] = {}
    mapped_region_codes: set[str] = set()
    for feature in mapped_geojson.get("features", []):
        properties = feature.get("properties", {})
        name_key = _normalized_column_name(properties.get("NAME_2", ""))
        boundary_names[name_key] = boundary_names.get(name_key, 0) + 1

    for feature in mapped_geojson.get("features", []):
        properties = feature.get("properties", {})
        code_key = _region_code_key(properties.get("CC_2"))
        region = result_by_code.get(code_key) if code_key is not None else None
        if region is None:
            name_key = _normalized_column_name(properties.get("NAME_2", ""))
            name_matches = result_by_name.get(name_key, [])
            if len(name_matches) == 1 and boundary_names.get(name_key) == 1:
                region = name_matches[0]
        if region is None:
            properties["cluster_label"] = "Belum ada data"
            properties["jumlah_meninggal"] = "—"
            properties["jiwa_terdampak"] = "—"
            properties["rumah_rusak"] = "—"
            continue
        mapped_region_codes.add(region["_kode_peta"])
        properties["cluster_label"] = region["Cluster"]
        properties["jumlah_meninggal"] = f"{region[FEATURE_LABELS[0]]:,.0f}"
        properties["jiwa_terdampak"] = f"{region[FEATURE_LABELS[1]]:,.0f}"
        properties["rumah_rusak"] = f"{region[FEATURE_LABELS[2]]:,.0f}"

    folium_map = folium.Map(
        location=[-2.5, 118.0],
        zoom_start=5,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )
    folium.GeoJson(
        mapped_geojson,
        name="Cluster kabupaten/kota",
        style_function=lambda feature: {
            "fillColor": color_map.get(
                feature["properties"].get("cluster_label"),
                "#cbd5e1",
            ),
            "color": "#ffffff",
            "weight": 0.45,
            "fillOpacity": 0.72,
        },
        highlight_function=lambda _: {
            "color": "#0f172a",
            "weight": 1.4,
            "fillOpacity": 0.9,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "NAME_2",
                "NAME_1",
                "CC_2",
                "cluster_label",
                "jumlah_meninggal",
                "jiwa_terdampak",
                "rumah_rusak",
            ],
            aliases=[
                "Kabupaten/kota:",
                "Provinsi:",
                "Kode wilayah:",
                "Cluster:",
                "Korban meninggal:",
                "Jiwa terdampak:",
                "Rumah rusak:",
            ],
            localize=True,
            sticky=False,
        ),
        show=True,
    ).add_to(folium_map)
    folium.LayerControl(collapsed=True).add_to(folium_map)

    st_folium(
        folium_map,
        width=1100,
        height=530,
        returned_objects=[],
        key="landslide_cluster_map",
    )
    return len(mapped_region_codes)


def _cluster_summary(result: pd.DataFrame) -> pd.DataFrame:
    """Hitung jumlah wilayah dan rata-rata dampak longsor untuk setiap cluster.

    Args:
        result: Data wilayah yang telah memiliki label ``Cluster`` dan fitur dampak.

    Returns:
        Ringkasan jumlah wilayah serta rata-rata korban dan kerusakan per cluster.
    """
    summary = (
        result.groupby("Cluster", as_index=False)
        .agg(
            **{
                "Jumlah Wilayah": ("Kabupaten", "count"),
                "Korban Meninggal": (FEATURE_LABELS[0], "mean"),
                "Jiwa Terdampak": (FEATURE_LABELS[1], "mean"),
                "Rumah Rusak": (FEATURE_LABELS[2], "mean"),
                "Fasilitas Umum Rusak": (FEATURE_LABELS[3], "mean"),
            }
        )
        .sort_values("Cluster", key=lambda values: values.map(
            lambda label: -1 if label == "Noise" else int(label.rsplit(" ", 1)[-1])
        ))
    )
    return summary


def _candidate_quality(evaluation_scores: dict[str, float | None]) -> float:
    """Gunakan Silhouette Score sebagai satu-satunya skor pemilihan kandidat."""
    silhouette = evaluation_scores.get("silhouette")
    if silhouette is None:
        return float("-inf")
    return float(silhouette)


def _pick_best_kmedoids(regions: pd.DataFrame, max_k: int = 7) -> dict[str, object]:
    """Cari k terbaik untuk K-Medoids berdasarkan silhouette score."""
    best_choice: dict[str, object] | None = None
    limit = min(max_k, max(2, len(regions) - 1))
    for cluster_count in range(2, limit + 1):
        candidate_result, candidate_scores, candidate_notes = cluster_regions(
            regions,
            method="K-Medoids",
            cluster_count=cluster_count,
            min_samples=5,
            xi=None,
        )
        score = _candidate_quality(candidate_scores)
        candidate = {
            "method": "K-Medoids",
            "cluster_count": cluster_count,
            "min_samples": 5,
            "xi": None,
            "result": candidate_result,
            "evaluation_scores": candidate_scores,
            "evaluation_notes": candidate_notes,
            "score": score,
        }
        if best_choice is None or candidate["score"] > best_choice["score"]:
            best_choice = candidate

    if best_choice is None:
        raise ValueError("Tidak ada kombinasi K-Medoids yang valid untuk dataset ini.")
    return best_choice


def _pick_best_optics(regions: pd.DataFrame, max_min_samples: int = 40) -> dict[str, object]:
    """Pilih OPTICS dengan cakupan terbesar di antara kandidat valid."""
    best_choice: dict[str, object] | None = None
    best_quality = (-1, float("-inf"))
    candidate_rows: list[dict[str, object]] = []
    max_min = min(max_min_samples, max(2, len(regions) - 1))
    xi_values = [round(value, 2) for value in np.arange(0.01, 0.20, 0.02)]
    for min_samples in range(2, max_min + 1):
        for xi in xi_values:
            candidate_result, candidate_scores, candidate_notes = cluster_regions(
                regions,
                method="OPTICS",
                cluster_count=3,
                min_samples=min_samples,
                xi=xi,
            )
            clustered_region_count = int(candidate_result["Cluster"].ne("Noise").sum())
            cluster_count = int(
                candidate_result.loc[
                    candidate_result["Cluster"].ne("Noise"), "Cluster"
                ].nunique()
            )
            silhouette = candidate_scores.get("silhouette")
            eligible = cluster_count >= 2 and silhouette is not None
            quality = (
                clustered_region_count,
                float(silhouette) if silhouette is not None else float("-inf"),
            ) if eligible else (-1, float("-inf"))
            candidate_row = {
                "Min samples": min_samples,
                "Xi": xi,
                "Wilayah ter-cluster": clustered_region_count,
                "Cluster terbentuk": cluster_count,
                "Silhouette Score": silhouette,
                "Layak": eligible,
                "Keterangan": (
                    "Kandidat valid"
                    if eligible
                    else (
                        "Ditolak: perlu minimal 2 cluster"
                        if cluster_count < 2
                        else "Ditolak: Silhouette Score tidak tersedia"
                    )
                ),
                "Terpilih": False,
            }
            candidate_rows.append(candidate_row)
            candidate = {
                "method": "OPTICS",
                "cluster_count": cluster_count,
                "min_samples": min_samples,
                "xi": xi,
                "result": candidate_result,
                "evaluation_scores": candidate_scores,
                "evaluation_notes": candidate_notes,
                "clustered_region_count": clustered_region_count,
                "score": quality,
                "candidate_rows": candidate_rows,
            }
            if eligible and quality > best_quality:
                best_choice = candidate
                best_quality = quality

    if best_choice is None:
        raise ValueError(
            "Tidak ditemukan konfigurasi OPTICS dengan minimal dua cluster dan "
            "Silhouette Score yang dapat dihitung."
        )
    for candidate_row in candidate_rows:
        candidate_row["Terpilih"] = (
            candidate_row["Min samples"] == best_choice["min_samples"]
            and candidate_row["Xi"] == best_choice["xi"]
        )
    best_choice["candidate_rows"] = candidate_rows
    return best_choice


def _cluster_profile(result: pd.DataFrame) -> pd.DataFrame:
    """Hitung rata-rata fitur untuk cluster valid, tanpa memasukkan label Noise."""
    clustered_regions = result.loc[result["Cluster"].ne("Noise")]
    if clustered_regions.empty:
        return pd.DataFrame(columns=["Cluster", *FEATURE_LABELS])

    profile = (
        clustered_regions.groupby("Cluster")[FEATURE_LABELS]
        .mean()
        .reset_index()
    )
    return profile.sort_values(
        "Cluster",
        key=lambda values: values.map(
            lambda label: int(label.rsplit(" ", 1)[-1])
        ),
    )


if not is_logged_in():
    require_login()
    st.stop()

show_sidebar(active_page="Clustering")

st.markdown(
    """
    <section class="cluster-hero">
        <div class="cluster-eyebrow">Analisis dampak · Indonesia · 2014–2025</div>
        <h1>Clustering Wilayah Tanah Longsor</h1>
        <p>
            Kelompokkan kabupaten/kota berdasarkan akumulasi dampak kejadian
            tanah longsor. Setiap wilayah dihitung dari data yang lolos
            pemeriksaan missing value, lalu dinormalisasi sebelum proses clustering.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

try:
    (
        _active_file_name,
        source_data,
        _dataset_is_in_database,
        dataset_version,
    ) = load_active_dataset()
except Exception as exc:
    st.error("Dataset tanah longsor gagal dimuat dari Neon atau file lokal.")
    st.caption(str(exc))
    st.stop()

if source_data.empty:
    st.error("Dataset tanah longsor tidak berisi data.")
    st.stop()

year_column = _find_column(source_data.columns, ("Tahun",))
if year_column is None:
    st.error("Kolom Tahun tidak ditemukan pada dataset.")
    st.stop()
available_years = sorted(
    int(year)
    for year in pd.to_numeric(source_data[year_column], errors="coerce")
    .dropna()
    .unique()
    if 2014 <= year <= 2025
)
if not available_years:
    st.error("Dataset tidak memiliki data pada periode 2014–2025.")
    st.stop()

experiment_tab, data_tab = st.tabs(["Eksperimen", "Informasi Data"])

with experiment_tab:
    top_metrics = st.columns(2)
    top_metrics[0].metric("Periode analisis", "2014–2025")
    top_metrics[1].metric("Kejadian pada dataset", f"{len(source_data):,}")

    st.markdown('<div class="section-kicker">Atur analisis</div>', unsafe_allow_html=True)
    with st.container(border=True):
        control_year, control_method, control_mode = st.columns([1, 1.2, 1.5])
        with control_year:
            year_options: list[str | int] = ["Semua tahun (2014–2025)", *available_years]
            selected_year_option = st.selectbox(
                "Filter tahun",
                year_options,
                help="Pilih satu tahun atau gabungkan seluruh data periode 2014–2025.",
            )
        with control_method:
            method = st.selectbox(
                "Metode clustering",
                ("K-Medoids", "OPTICS"),
                help="K-Medoids membagi wilayah ke k kelompok; OPTICS menemukan "
                "kelompok berbasis kepadatan dan dapat menandai noise.",
            )
        with control_mode:
            cluster_mode = st.selectbox(
                "Mode pencarian parameter",
                ("Cari konfigurasi terbaik", "Gunakan parameter manual"),
                index=0,
                help="Pilih otomatis untuk mencari konfigurasi terbaik; kriteria mengikuti metode yang dipilih, "
                "atau manual jika ingin menentukan nilai parameter sendiri.",
            )

    selected_year = (
        None
        if selected_year_option == "Semua tahun (2014–2025)"
        else int(selected_year_option)
    )
    parameter_columns = st.columns([1, 1, 1.2])
    if method == "K-Medoids":
        if cluster_mode == "Gunakan parameter manual":
            with parameter_columns[0]:
                cluster_count = st.slider(
                    "Jumlah cluster (k)",
                    min_value=2,
                    max_value=12,
                    value=3,
                    help="Jumlah kelompok yang akan dibentuk.",
                )
            min_samples = 5
            xi = None
            with parameter_columns[1]:
                st.caption("K-Medoids menggunakan jarak Euclidean pada fitur yang dinormalisasi.")
        else:
            cluster_count = 3
            min_samples = 5
            xi = None
            with parameter_columns[0]:
                st.caption("Aplikasi akan mencari k terbaik dari 2 sampai 7 berdasarkan silhouette score.")
            with parameter_columns[1]:
                st.caption("Parameter terbaik akan dipilih otomatis untuk hasil clustering yang paling stabil.")
            with parameter_columns[2]:
                st.caption("Mode ini cocok untuk skripsi karena hasil didasarkan pada evaluasi objektif, bukan asumsi manual.")
    else:
        cluster_count = 3
        if cluster_mode == "Gunakan parameter manual":
            use_custom_xi = st.checkbox(
                "Atur xi (opsional)",
                value=False,
                help="Jika tidak diatur, OPTICS memakai nilai xi bawaan scikit-learn (0,05).",
            )
            with parameter_columns[0]:
                min_samples = st.slider(
                    "Min samples",
                    min_value=2,
                    max_value=40,
                    value=5,
                    help="Jumlah minimum sampel untuk membentuk wilayah padat.",
                )
            with parameter_columns[1]:
                if use_custom_xi:
                    xi = st.slider(
                        "Xi",
                        min_value=0.01,
                        max_value=0.20,
                        value=0.05,
                        step=0.01,
                        help="Ambang sensitivitas ekstraksi cluster OPTICS metode xi.",
                    )
                else:
                    xi = None
                    st.caption("Menggunakan xi bawaan scikit-learn: 0,05.")
            with parameter_columns[2]:
                st.caption("OPTICS dapat menandai wilayah yang tidak masuk kelompok sebagai noise.")
        else:
            min_samples = 5
            xi = None
            with parameter_columns[0]:
                st.caption("Grid otomatis: min_samples 2–40 (atau sampai jumlah wilayah−1), xi 0,01–0,19 dengan interval 0,02.")
            with parameter_columns[1]:
                st.caption("Syarat: minimal 2 cluster dan Silhouette Score tersedia. Terbanyak wilayah non-noise menang; silhouette memecahkan seri.")
            with parameter_columns[2]:
                st.caption("Semua kandidat beserta jumlah cluster, cakupan, dan skor akan ditampilkan setelah proses.")

    run_analysis = st.button(
        "Jalankan clustering",
        type="primary",
        icon=":material/play_arrow:",
        width="stretch",
    )

    st.markdown(
        """
        <div class="cluster-note">
            Fitur cluster hanya mencakup korban, jiwa terdampak, rumah rusak, dan
            fasilitas umum rusak.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if run_analysis:
        try:
            with st.spinner(
                f"Menyiapkan data dan menjalankan {method}. Proses ini bisa memerlukan waktu..."
            ):
                regional_data, dropped_rows, valid_event_rows = prepare_regional_data(
                    source_data,
                    selected_year,
                )
                computation_started = time.perf_counter()
                search_candidates = None
                if cluster_mode == "Cari konfigurasi terbaik":
                    if method == "K-Medoids":
                        best_choice = _pick_best_kmedoids(regional_data)
                        clustering_result = best_choice["result"]
                        evaluation_scores = best_choice["evaluation_scores"]
                        evaluation_notes = best_choice["evaluation_notes"]
                        cluster_count = int(best_choice["cluster_count"])
                        min_samples = int(best_choice["min_samples"])
                        xi = best_choice["xi"]
                    else:
                        best_choice = _pick_best_optics(regional_data)
                        clustering_result = best_choice["result"]
                        evaluation_scores = best_choice["evaluation_scores"]
                        evaluation_notes = best_choice["evaluation_notes"]
                        cluster_count = int(best_choice["cluster_count"])
                        min_samples = int(best_choice["min_samples"])
                        xi = best_choice["xi"]
                        search_candidates = best_choice["candidate_rows"]
                else:
                    clustering_result, evaluation_scores, evaluation_notes = cluster_regions(
                        regional_data,
                        method,
                        cluster_count,
                        min_samples,
                        xi,
                    )
                computation_seconds = time.perf_counter() - computation_started
        except ImportError as exc:
            st.error(
                "Pustaka clustering belum tersedia. Pasang dependensi aplikasi "
                "dari requirement.txt, termasuk scikit-learn dan "
                "scikit-learn-extra untuk K-Medoids."
            )
            st.caption(str(exc))
            st.session_state.pop("clustering_result", None)
            st.session_state.pop("clustering_metadata", None)
        except ValueError as exc:
            st.error(f"Proses clustering tidak dapat dijalankan: {exc}")
            st.session_state.pop("clustering_result", None)
            st.session_state.pop("clustering_metadata", None)
        else:
            st.session_state["clustering_result"] = clustering_result
            st.session_state["clustering_metadata"] = {
                "method": method,
                "year": selected_year,
                "dataset_version": dataset_version,
                "cluster_count": cluster_count,
                "min_samples": min_samples,
                "xi": xi,
                "optics_mode": "xi",
                "dropped_rows": dropped_rows,
                "valid_event_rows": valid_event_rows,
                "evaluation_scores": evaluation_scores,
                "evaluation_notes": evaluation_notes,
                "computation_seconds": computation_seconds,
                "cluster_mode": cluster_mode,
                "search_candidates": search_candidates,
            }

    result = st.session_state.get("clustering_result")
    metadata = st.session_state.get("clustering_metadata")
    if result is None or metadata is None:
        st.info(
            "Pilih filter dan metode, lalu tekan **Jalankan clustering** untuk "
            "melihat hasil analisis wilayah."
        )
        result = None
    elif (
        metadata["method"] != method
        or metadata["year"] != selected_year
        or metadata.get("dataset_version") != dataset_version
        or metadata.get("cluster_mode") != cluster_mode
        or (
            cluster_mode == "Gunakan parameter manual"
            and (
                metadata["cluster_count"] != cluster_count
                or metadata["min_samples"] != min_samples
                or metadata.get("xi") != xi
            )
        )
        or metadata.get("optics_mode") != "xi"
    ):
        st.info("Pengaturan berubah. Jalankan clustering kembali untuk memperbarui hasil.")
        result = None

    if result is not None and metadata is not None:
        cluster_parameters = (
            f"k={metadata['cluster_count']}"
            if metadata["method"] == "K-Medoids"
            else (
                f"min_samples={metadata['min_samples']}, xi="
                f"{metadata['xi']:.2f}"
                if metadata.get("xi") is not None
                else f"min_samples={metadata['min_samples']}, xi=bawaan 0,05"
            )
        )
        if metadata.get("cluster_mode") == "Cari konfigurasi terbaik":
            cluster_parameters += " (terbaik otomatis)"
        non_noise_clusters = [
            label for label in result["Cluster"].unique() if label != "Noise"
        ]
        noise_count = int(result["Cluster"].eq("Noise").sum())
        summary_metrics = st.columns(3)
        summary_metrics[0].metric("Kabupaten/kota dianalisis", f"{len(result):,}")
        summary_metrics[1].metric("Cluster terbentuk", f"{len(non_noise_clusters):,}")
        summary_metrics[2].metric("Wilayah noise", f"{noise_count:,}")

        st.caption(
            f"Metode **{metadata['method']}** · "
            f"{'Semua tahun 2014–2025' if metadata['year'] is None else 'Tahun ' + str(metadata['year'])} · "
            f"{cluster_parameters} · "
            f"{metadata['valid_event_rows']:,} baris kejadian valid · "
            f"{metadata['dropped_rows']:,} baris dihapus karena missing atau nilai tidak valid pada fitur yang digunakan."
        )

        if (
            metadata["method"] == "OPTICS"
            and metadata.get("cluster_mode") == "Cari konfigurasi terbaik"
            and metadata.get("search_candidates")
        ):
            candidate_table = pd.DataFrame(metadata["search_candidates"])
            candidate_table = candidate_table.sort_values(
                ["Layak", "Wilayah ter-cluster", "Silhouette Score"],
                ascending=[False, False, False],
                na_position="last",
                kind="stable",
            )
            with st.expander("Detail pencarian konfigurasi OPTICS"):
                st.caption(
                    f"{len(candidate_table):,} kombinasi diuji. Konfigurasi dipilih "
                    "dari kandidat yang membentuk minimal 2 cluster dan memiliki "
                    "Silhouette Score terhitung; cakupan non-noise tertinggi menang, "
                    "lalu Silhouette Score menjadi pemecah seri."
                )
                st.dataframe(
                    candidate_table,
                    hide_index=True,
                    width="stretch",
                    height=360,
                    column_config={
                        "Min samples": st.column_config.NumberColumn(format="%d"),
                        "Xi": st.column_config.NumberColumn(format="%.2f"),
                        "Wilayah ter-cluster": st.column_config.NumberColumn(format="%d"),
                        "Cluster terbentuk": st.column_config.NumberColumn(format="%d"),
                        "Silhouette Score": st.column_config.NumberColumn(format="%.4f"),
                    },
                )

        st.subheader("Evaluasi hasil clustering")
        evaluation_scores = metadata["evaluation_scores"]
        silhouette = evaluation_scores["silhouette"]
        if silhouette is None:
            silhouette_interpretation = metadata["evaluation_notes"]["silhouette"]
            silhouette_color = "gray"
        elif silhouette >= 0.71:
            silhouette_interpretation = (
                "Struktur kuat: anggota dalam cluster cenderung berdekatan dan "
                "cluster relatif terpisah."
            )
            silhouette_color = "green"
        elif silhouette >= 0.51:
            silhouette_interpretation = (
                "Struktur sedang: cluster cukup terlihat, meski masih ada "
                "kemiripan antarcluster."
            )
            silhouette_color = "yellow"
        elif silhouette >= 0.26:
            silhouette_interpretation = (
                "Struktur lemah: pemisahan cluster belum kuat dan beberapa "
                "wilayah mungkin mirip dengan cluster lain."
            )
            silhouette_color = "orange"
        else:
            silhouette_interpretation = (
                "Belum ada struktur cluster yang jelas. Nilai negatif menunjukkan "
                "sebagian wilayah mungkin lebih dekat ke cluster lain."
            )
            silhouette_color = "red"

        evaluation_columns = st.columns(2, gap="medium")
        with evaluation_columns[0]:
            with st.container(border=True):
                st.metric(
                    "Silhouette Score",
                    f"{silhouette:.4f}" if silhouette is not None else "N/A",
                    help=(
                        "Rentang -1 sampai 1. Nilai mendekati 1 berarti wilayah "
                        "lebih mirip dengan cluster sendiri daripada cluster lain."
                    ),
                )
                if silhouette_interpretation:
                    st.markdown(
                        f":{silhouette_color}[**{silhouette_interpretation}**]"
                    )
        with evaluation_columns[1]:
            with st.container(border=True):
                davies_bouldin = evaluation_scores["davies_bouldin"]
                st.metric(
                    "Davies–Bouldin Index",
                    f"{davies_bouldin:.4f}" if davies_bouldin is not None else "N/A",
                )
                st.caption(
                    "Semakin kecil nilainya, semakin kompak dan semakin terpisah "
                    "cluster. Gunakan untuk membandingkan hasil pada data dan "
                    "metode yang sama."
                )

        with st.container(border=True):
            st.metric(
                "Waktu komputasi (detik)",
                f"{metadata['computation_seconds']:.4f}",
                help=(
                    "Waktu untuk proses clustering, termasuk normalisasi fitur "
                    "dan perhitungan metrik evaluasi."
                ),
            )
        with st.container(border=True):
            st.markdown("**Panduan membaca Silhouette Score**")
            st.markdown(
                "- :green[**0,71–1,00 · Struktur kuat**] — cluster terpisah dengan baik.\n"
                "- :yellow[**0,51–0,70 · Struktur sedang**] — pemisahan cukup terlihat.\n"
                "- :orange[**0,26–0,50 · Struktur lemah**] — cluster masih berdekatan.\n"
                "- :red[**Di bawah 0,26 · Struktur belum jelas**] — nilai negatif "
                "dapat menandakan sebagian wilayah lebih cocok di cluster lain."
            )

        unavailable_metrics = [
            note
            for note in metadata["evaluation_notes"].values()
            if note is not None
        ]
        if unavailable_metrics:
            st.info(
                "Metrik tidak dapat dihitung: "
                + " ".join(dict.fromkeys(unavailable_metrics))
            )

        st.divider()
        st.subheader("Ringkasan kategori mean cluster")
        st.dataframe(
            _cluster_summary(result),
            hide_index=True,
            width="stretch",
            column_config={
                "Jumlah Wilayah": st.column_config.NumberColumn(format="%d"),
                "Korban Meninggal": st.column_config.NumberColumn(format="%d"),
                "Jiwa Terdampak": st.column_config.NumberColumn(format="%d"),
                "Rumah Rusak": st.column_config.NumberColumn(format="%d"),
                "Fasilitas Umum Rusak": st.column_config.NumberColumn(format="%d"),
            },
        )

        st.subheader("Ringkasan karakteristik cluster")
        st.caption(
            "Setiap indikator membandingkan rata-rata cluster dengan rata-rata "
            "nilai cluster non-noise lainnya. Label cluster bukan tingkat kerawanan."
        )
        cluster_profile = _cluster_profile(result)
        if cluster_profile.empty:
            st.info(
                "Belum ada cluster non-noise yang dapat diprofilkan. "
                "Pada metode OPTICS, periksa kembali parameter jika semua wilayah "
                "tergolong noise."
            )
        else:
            cluster_sizes = result.loc[result["Cluster"].ne("Noise")].groupby(
                "Cluster"
            ).size()
            profile_columns = st.columns(2, gap="medium")
            for cluster_index, (_, profile_row) in enumerate(
                cluster_profile.iterrows()
            ):
                cluster_name = str(profile_row["Cluster"])
                other_clusters = cluster_profile.loc[
                    cluster_profile["Cluster"].ne(cluster_name)
                ]
                with profile_columns[cluster_index % len(profile_columns)]:
                    with st.container(border=True):
                        st.markdown(f"### :blue[{cluster_name}]")
                        st.caption(
                            f"{cluster_sizes.get(cluster_name, 0):,} kabupaten/kota"
                        )
                        if other_clusters.empty:
                            st.markdown(
                                "Belum dapat dibandingkan karena hanya ada satu "
                                "cluster non-noise."
                            )
                            continue

                        for feature in FEATURE_LABELS:
                            cluster_mean = float(profile_row[feature])
                            other_cluster_mean = float(other_clusters[feature].mean())
                            if np.isclose(
                                cluster_mean,
                                other_cluster_mean,
                                rtol=1e-9,
                                atol=1e-9,
                            ):
                                comparison = "setara dengan"
                            elif cluster_mean > other_cluster_mean:
                                comparison = "lebih tinggi daripada"
                            else:
                                comparison = "lebih rendah daripada"
                            st.markdown(
                                f"- **{feature}**: {cluster_mean:,.2f}, "
                                f"{comparison} rata-rata cluster lain "
                                f"({other_cluster_mean:,.2f})."
                            )
        if noise_count:
            st.info(
                f"{noise_count:,} wilayah berlabel Noise tidak disertakan dalam "
                "profil karena tidak termasuk ke cluster yang terbentuk."
            )

        st.subheader("Distribusi wilayah per cluster")
        st.caption(
            "Grafik menunjukkan jumlah dan proporsi kabupaten/kota pada "
            "setiap cluster. Label cluster bukan tingkat kerawanan."
        )
        cluster_distribution = (
            result.groupby("Cluster", as_index=False)
            .size()
            .rename(columns={"size": "Jumlah Kabupaten/Kota"})
        )
        cluster_order = sorted(
            cluster_distribution["Cluster"].tolist(),
            key=lambda label: (
                -1 if label == "Noise" else int(label.rsplit(" ", 1)[-1])
            ),
        )
        cluster_distribution["Urutan"] = cluster_distribution["Cluster"].map(
            {label: index for index, label in enumerate(cluster_order)}
        )
        total_tenths = 1000
        exact_tenths = (
            cluster_distribution["Jumlah Kabupaten/Kota"] / len(result) * total_tenths
        )
        rounded_tenths = exact_tenths.astype(int)
        remaining_tenths = total_tenths - int(rounded_tenths.sum())
        largest_remainders = (
            exact_tenths - rounded_tenths
        ).sort_values(ascending=False, kind="stable")
        for index in largest_remainders.index[:remaining_tenths]:
            rounded_tenths.loc[index] += 1

        cluster_distribution["Persentase"] = (
            cluster_distribution["Jumlah Kabupaten/Kota"] / len(result) * 100
        )
        cluster_distribution["Label Persentase"] = (
            rounded_tenths.map(lambda value: f"{value // 10}.{value % 10}%")
        )
        cluster_colors = [
            "#64748b"
            if label == "Noise"
            else CLUSTER_PALETTE[
                (int(label.rsplit(" ", 1)[-1]) - 1) % len(CLUSTER_PALETTE)
            ]
            for label in cluster_order
        ]
        distribution_left, distribution_right = st.columns(2, gap="medium")
        with distribution_left:
            st.markdown("**Jumlah kabupaten/kota**")
            st.vega_lite_chart(
                cluster_distribution,
                {
                    "width": "container",
                    "height": 330,
                    "mark": {"type": "bar", "cornerRadiusTopLeft": 5, "cornerRadiusTopRight": 5},
                    "encoding": {
                        "x": {
                            "field": "Cluster",
                            "type": "ordinal",
                            "sort": cluster_order,
                            "axis": {"title": "Cluster", "labelAngle": -35},
                        },
                        "y": {
                            "field": "Jumlah Kabupaten/Kota",
                            "type": "quantitative",
                            "axis": {"title": "Jumlah wilayah"},
                        },
                        "color": {
                            "field": "Cluster",
                            "type": "nominal",
                            "scale": {
                                "domain": cluster_order,
                                "range": cluster_colors,
                            },
                            "legend": None,
                        },
                        "tooltip": [
                            {"field": "Cluster", "type": "nominal"},
                            {
                                "field": "Jumlah Kabupaten/Kota",
                                "type": "quantitative",
                            },
                            {
                                "field": "Persentase",
                                "type": "quantitative",
                                "format": ".2f",
                            },
                        ],
                    },
                    "config": {
                        "view": {"stroke": None},
                        "axis": {"labelAngle": -35},
                    },
                },
                width="stretch",
                key="cluster_distribution_bar",
            )
        with distribution_right:
            st.markdown("**Proporsi kabupaten/kota**")
            st.vega_lite_chart(
                cluster_distribution,
                {
                    "width": "container",
                    "height": 330,
                    "layer": [
                        {
                            "mark": {"type": "arc", "outerRadius": 125},
                            "encoding": {
                                "theta": {
                                    "field": "Jumlah Kabupaten/Kota",
                                    "type": "quantitative",
                                    "stack": True,
                                },
                                "order": {
                                    "field": "Urutan",
                                    "type": "ordinal",
                                    "sort": "ascending",
                                },
                                "color": {
                                    "field": "Cluster",
                                    "type": "nominal",
                                    "scale": {
                                        "domain": cluster_order,
                                        "range": cluster_colors,
                                    },
                                    "legend": {"title": None, "orient": "bottom"},
                                },
                                "tooltip": [
                                    {"field": "Cluster", "type": "nominal"},
                                    {
                                        "field": "Jumlah Kabupaten/Kota",
                                        "type": "quantitative",
                                    },
                                    {
                                        "field": "Persentase",
                                        "type": "quantitative",
                                        "format": ".2f",
                                    },
                                ],
                            },
                        },
                        {
                            "mark": {
                                "type": "text",
                                "radius": 78,
                                "fontSize": 13,
                                "fontWeight": "bold",
                                "color": "white",
                            },
                            "encoding": {
                                "theta": {
                                    "field": "Jumlah Kabupaten/Kota",
                                    "type": "quantitative",
                                    "stack": True,
                                },
                                "order": {
                                    "field": "Urutan",
                                    "type": "ordinal",
                                    "sort": "ascending",
                                },
                                "text": {"field": "Label Persentase"},
                            },
                        },
                    ],
                },
                width="stretch",
                key="cluster_distribution_pie",
            )

        st.subheader("Persebaran dampak per cluster")
        chart_left, chart_right = st.columns(2)
        with chart_left:
            st.markdown("**Jiwa terdampak dan rumah rusak**")
            st.scatter_chart(
                result,
                x=FEATURE_LABELS[1],
                y=FEATURE_LABELS[2],
                color="Cluster",
                width="stretch",
                height=390,
                x_label="Jiwa terdampak",
                y_label="Total rumah rusak",
            )
        with chart_right:
            st.markdown("**Korban meninggal dan fasilitas umum rusak**")
            st.scatter_chart(
                result,
                x=FEATURE_LABELS[0],
                y=FEATURE_LABELS[3],
                color="Cluster",
                width="stretch",
                height=390,
                x_label="Jumlah korban meninggal",
                y_label="Total fasilitas umum rusak",
            )
        st.caption(
            "Setiap titik mewakili satu kabupaten/kota. Nilai pada grafik adalah akumulasi "
            "dampak pada rentang tahun yang dipilih."
        )

        st.subheader("Boxplot distribusi indikator per cluster")
        st.caption(
            "Box menunjukkan median dan sebaran dampak antarwilayah dalam setiap "
            "cluster. Titik di luar whisker menandai kemungkinan nilai ekstrem."
        )
        for row_start in range(0, len(FEATURE_LABELS), 2):
            boxplot_columns = st.columns(2, gap="medium")
            for column, feature_index in zip(
                boxplot_columns,
                range(row_start, min(row_start + 2, len(FEATURE_LABELS))),
            ):
                feature = FEATURE_LABELS[feature_index]
                with column:
                    with st.container(border=True):
                        st.markdown(f"**Distribusi {feature}**")
                        st.vega_lite_chart(
                            result[["Cluster", feature]],
                            {
                                "width": "container",
                                "height": 330,
                                "mark": {"type": "boxplot", "extent": 1.5},
                                "encoding": {
                                    "x": {
                                        "field": "Cluster",
                                        "type": "nominal",
                                        "sort": cluster_order,
                                        "axis": {"title": "Cluster"},
                                    },
                                    "y": {
                                        "field": feature,
                                        "type": "quantitative",
                                        "axis": {"title": feature},
                                    },
                                    "color": {
                                        "field": "Cluster",
                                        "type": "nominal",
                                        "scale": {
                                            "domain": cluster_order,
                                            "range": cluster_colors,
                                        },
                                        "legend": None,
                                    },
                                },
                                "config": {"view": {"stroke": None}},
                            },
                            width="stretch",
                            key=f"cluster_indicator_boxplot_{feature_index}",
                            alt=f"Distribusi {feature.casefold()} pada setiap cluster",
                        )

        st.subheader("Peta persebaran wilayah")
        map_legend = [
            f'<span style="display:inline-flex;align-items:center;margin:0 .8rem .35rem 0;'
            f'font-size:.84rem"><span style="display:inline-block;width:.7rem;height:.7rem;'
            f'border-radius:50%;background:{_cluster_color(label)};'
            f'margin-right:.35rem"></span>{label}</span>'
            for label in sorted(
                non_noise_clusters,
                key=lambda cluster: int(cluster.rsplit(" ", 1)[-1]),
            )
        ]
        if noise_count:
            map_legend.append(
                '<span style="display:inline-flex;align-items:center;margin:0 .8rem .35rem 0;'
                'font-size:.84rem"><span style="display:inline-block;width:.7rem;height:.7rem;'
                'border-radius:50%;background:#64748b;margin-right:.35rem"></span>Noise</span>'
            )
        st.markdown("".join(map_legend), unsafe_allow_html=True)
        st.caption(
            "Warna menunjukkan label cluster; arahkan kursor ke wilayah untuk melihat "
            "ringkasan dampaknya. Wilayah yang tidak tercocokkan dengan batas peta "
            "ditampilkan dengan warna abu-abu."
        )
        try:
            if not GEOJSON_PATH.is_file():
                raise FileNotFoundError(f"Berkas batas wilayah tidak ditemukan: {GEOJSON_PATH}")
            mapped_region_count = render_cluster_map(result)
            if mapped_region_count < len(result):
                st.info(
                    f"Batas peta tersedia untuk {mapped_region_count:,} dari {len(result):,} "
                    "wilayah pada hasil. Wilayah lain tetap tercantum pada tabel, tetapi "
                    "batas geografisnya tidak tersedia pada GeoJSON aplikasi."
                )
        except ImportError as exc:
            st.error(
                "Pustaka peta belum tersedia. Pasang dependensi aplikasi dari "
                "requirement.txt, termasuk folium dan streamlit-folium."
            )
            st.caption(str(exc))
        except (OSError, ValueError, KeyError) as exc:
            st.error("Peta persebaran wilayah gagal ditampilkan.")
            st.caption(str(exc))

        st.subheader("Tabel hasil clustering per kabupaten/kota")
        table_columns = [
            "Kode Kabupaten",
            "Kabupaten",
            *FEATURE_LABELS,
            "Cluster",
        ]
        table_result = result[table_columns].sort_values(
            ["Cluster", "Kabupaten"],
            kind="stable",
        )
        st.dataframe(
            table_result,
            hide_index=True,
            width="stretch",
            height=460,
            column_config={
                "Kode Kabupaten": st.column_config.TextColumn("Kode Kabupaten"),
                "Jumlah Korban Meninggal": st.column_config.NumberColumn(format="%d"),
                "Jiwa Terdampak": st.column_config.NumberColumn(format="%d"),
                "Total Rumah Rusak": st.column_config.NumberColumn(format="%d"),
                "Total Fasilitas Umum Rusak": st.column_config.NumberColumn(format="%d"),
            },
        )

        download_columns = [
            "Kode Kabupaten",
            "Kabupaten",
            *FEATURE_LABELS,
            "Cluster",
        ]
        st.download_button(
            "Unduh hasil sebagai CSV",
            data=result[download_columns].to_csv(index=False).encode("utf-8-sig"),
            file_name="hasil_clustering_longsor.csv",
            mime="text/csv",
            icon=":material/download:",
        )

with data_tab:
    st.subheader("Top kabupaten/kota terdampak per tahun")
    st.caption(
        "Peringkat dihitung dari akumulasi dampak kejadian longsor di setiap "
        "kabupaten/kota. Pilih jenis dampak untuk melihat tren tahunan dan wilayah "
        "dengan dampak tertinggi."
    )
    information_feature = st.selectbox(
        "Jenis dampak",
        FEATURE_LABELS,
        key="annual_top_feature",
    )

    annual_top_tables = []
    annual_totals = []
    annual_region_by_year = {}
    for year in available_years:
        try:
            annual_regions, _, _ = prepare_regional_data(source_data, year)
        except ValueError as exc:
            st.warning(f"Ringkasan tahun {year} tidak tersedia: {exc}")
            continue

        annual_region_by_year[year] = annual_regions
        annual_totals.append(
            {
                "Tahun": year,
                "Total dampak": annual_regions[information_feature].sum(),
            }
        )
        annual_top = annual_regions.nlargest(5, information_feature)[
            ["Kode Kabupaten", "Kabupaten", information_feature]
        ].copy()
        annual_top.insert(0, "Tahun", year)
        annual_top.insert(1, "Peringkat", range(1, len(annual_top) + 1))
        annual_top_tables.append(
            annual_top.rename(columns={information_feature: "Total dampak"})
        )

    if annual_top_tables:
        information_year = st.selectbox(
            "Tahun untuk peringkat wilayah",
            list(annual_region_by_year),
            index=len(annual_region_by_year) - 1,
            key="annual_top_year",
        )
        trend_column, top_region_column = st.columns(2)
        with trend_column:
            st.markdown(f"**Tren tahunan: {information_feature.casefold()}**")
            st.line_chart(
                pd.DataFrame(annual_totals),
                x="Tahun",
                y="Total dampak",
                x_label="Tahun",
                y_label="Total dampak",
                height=350,
                alt=f"Tren tahunan {information_feature.casefold()} untuk semua kabupaten/kota",
            )

        with top_region_column:
            selected_year_data = annual_region_by_year[information_year]
            top_regions = selected_year_data.nlargest(10, information_feature)
            st.markdown(
                f"**10 wilayah teratas, {information_year}: "
                f"{information_feature.casefold()}**"
            )
            st.bar_chart(
                top_regions.set_index("Kabupaten")[information_feature],
                horizontal=True,
                x_label=information_feature,
                y_label="Kabupaten/kota",
                height=350,
                alt=(
                    f"Sepuluh kabupaten/kota dengan {information_feature.casefold()} "
                    f"tertinggi pada {information_year}"
                ),
            )
    else:
        st.info("Belum ada data valid untuk membuat peringkat tahunan.")