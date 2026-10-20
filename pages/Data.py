from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from pandas.api.types import is_numeric_dtype

from components.auth import is_admin, is_logged_in, require_login
from components.dataset_store import load_active_dataset, save_active_dataset
from components.sidebar import show_sidebar


st.set_page_config(
    page_title="Dataset Tanah Longsor",
    page_icon="🗂️",
    layout="wide",
)

DATASET_PERIOD = "2014–2025"


def read_uploaded_dataset(file_name: str, content: bytes) -> pd.DataFrame:
    extension = Path(file_name).suffix.lower()
    if extension == ".csv":
        try:
            return pd.read_csv(
                io.BytesIO(content),
                sep=None,
                engine="python",
                encoding="utf-8-sig",
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                io.BytesIO(content),
                sep=None,
                engine="python",
                encoding="cp1252",
            )
    if extension == ".xlsx":
        return pd.read_excel(io.BytesIO(content), engine="openpyxl")
    raise ValueError("Format berkas tidak didukung. Gunakan CSV atau XLSX.")


def create_dataset_template(columns: pd.Index) -> bytes:
    template = pd.DataFrame(columns=columns)
    buffer = io.BytesIO()
    template.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def validate_dataset(
    uploaded: pd.DataFrame,
    current: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    candidate = uploaded.copy()
    errors: list[str] = []
    warnings: list[str] = []

    if candidate.empty or candidate.shape[1] == 0:
        return candidate, ["Berkas tidak berisi baris atau kolom data."], warnings

    if any(not str(column).strip() for column in candidate.columns):
        errors.append("Semua kolom harus memiliki nama.")

    duplicate_columns = candidate.columns[candidate.columns.duplicated()].tolist()
    if duplicate_columns:
        errors.append(
            "Nama kolom duplikat ditemukan: "
            + ", ".join(str(column) for column in duplicate_columns)
            + "."
        )

    expected_columns = set(current.columns)
    uploaded_columns = set(candidate.columns)
    missing_columns = [
        str(column)
        for column in current.columns
        if column not in uploaded_columns
    ]
    if missing_columns:
        errors.append(
            "Kolom wajib dari dataset penelitian tidak ditemukan: "
            + ", ".join(missing_columns)
            + "."
        )

    extra_columns = [
        str(column)
        for column in candidate.columns
        if column not in expected_columns
    ]
    if extra_columns:
        warnings.append(
            "Kolom tambahan akan dipertahankan: "
            + ", ".join(extra_columns)
            + "."
        )

    if candidate.dropna(how="all").empty:
        errors.append("Dataset hanya berisi baris kosong.")
        return candidate, errors, warnings

    numeric_columns = [
        column
        for column in current.columns
        if column in candidate.columns and is_numeric_dtype(current[column])
    ]
    converted_columns: list[str] = []
    for column in numeric_columns:
        original_values = candidate[column]
        converted_values = pd.to_numeric(original_values, errors="coerce")
        invalid_values = original_values.notna() & converted_values.isna()
        if invalid_values.any():
            errors.append(
                f"Kolom numerik “{column}” memiliki "
                f"{int(invalid_values.sum())} nilai yang tidak dapat dibaca sebagai angka."
            )
            continue

        numeric_values = converted_values.dropna().to_numpy(dtype=float)
        if numeric_values.size and not np.isfinite(numeric_values).all():
            errors.append(
                f"Kolom numerik “{column}” memiliki nilai tak hingga "
                "yang tidak dapat digunakan untuk clustering."
            )
            continue
        if not is_numeric_dtype(original_values):
            converted_columns.append(str(column))
        candidate[column] = converted_values

    if converted_columns:
        warnings.append(
            "Kolom berikut dibaca sebagai teks dan akan disimpan sebagai angka: "
            + ", ".join(converted_columns)
            + "."
        )

    missing_cells = int(candidate.isna().sum().sum())
    if missing_cells:
        affected_columns = int(candidate.isna().any(axis=0).sum())
        warnings.append(
            f"Ditemukan {missing_cells:,} nilai kosong pada "
            f"{affected_columns} kolom. Nilai kosong tidak diisi otomatis."
        )

    duplicate_rows = int(candidate.duplicated().sum())
    if duplicate_rows:
        warnings.append(
            f"Ditemukan {duplicate_rows:,} baris duplikat. "
            "Baris tidak dihapus otomatis."
        )

    return candidate, errors, warnings


def find_region_column(dataset: pd.DataFrame) -> str | None:
    candidates = [
        str(column)
        for column in dataset.columns
        if re.search(r"kabupaten|kab\.|kota|wilayah|daerah|region|city", str(column), re.I)
        and not re.search(r"kode|code", str(column), re.I)
    ]
    return candidates[0] if candidates else None


def display_file_size(size: int) -> str:
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.2f} MB"


if not is_logged_in():
    require_login()
    st.stop()

show_sidebar()

if not is_admin():
    st.error("Akses ditolak. Halaman Dataset hanya dapat diakses oleh Admin.")
    st.stop()

st.title("Dataset Tanah Longsor")
st.write(
    "Lihat dan kelola dataset yang digunakan untuk mengelompokkan wilayah "
    "berdasarkan karakteristik dampak tanah longsor."
)

success_message = st.session_state.pop("dataset_success_message", None)
if success_message:
    st.success(success_message)

try:
    (
        active_file_name,
        active_dataset,
        dataset_is_in_database,
        _dataset_version,
    ) = load_active_dataset()
except ImportError:
    st.error(
        "Pustaka database atau pembaca Excel belum tersedia. Pastikan "
        "SQLAlchemy, psycopg2-binary, dan xlrd terpasang."
    )
    st.stop()
except Exception as exc:
    st.error(
        "Dataset aktif gagal dimuat dari Neon atau file lokal. Periksa "
        "koneksi database, tabel active_dataset, dan berkas dataset."
    )
    st.caption(f"Detail: {exc}")
    st.stop()

if active_dataset.empty or active_dataset.shape[1] == 0:
    st.error("Dataset aktif tidak berisi baris atau kolom data.")
    st.stop()

region_column = find_region_column(active_dataset)
region_count = (
    int(active_dataset[region_column].nunique(dropna=True))
    if region_column is not None
    else None
)
region_value = f"{region_count:,}" if region_count is not None else "Tidak tersedia"

metric_columns = st.columns(4)
metric_columns[0].metric("Jumlah baris", f"{len(active_dataset):,}")
metric_columns[1].metric("Jumlah kolom", f"{len(active_dataset.columns):,}")
metric_columns[2].metric("Kabupaten/kota", region_value)
metric_columns[3].metric(
    "Periode data",
    DATASET_PERIOD,
    help="Rentang periode: 1 Januari 2014 sampai 31 Desember 2025.",
)

dataset_source = (
    f"Neon · {active_file_name}"
    if dataset_is_in_database
    else f"File lokal · {active_file_name} (akan disimpan ke Neon saat upload)"
)
st.caption(f"Sumber dataset aktif: `{dataset_source}`")
if region_column is None:
    st.info(
        "Jumlah wilayah tidak dapat dihitung karena kolom nama wilayah "
        "tidak ditemukan pada dataset."
    )

st.subheader("Data yang digunakan")
search_query = st.text_input(
    "Cari data",
    placeholder="Cari kata atau nilai pada seluruh kolom...",
)
row_limit = st.selectbox(
    "Jumlah baris yang ditampilkan",
    options=[10, 25, 50, 100, 250, 500],
    index=2,
)

filtered_dataset = active_dataset
if search_query:
    matching_rows = pd.Series(False, index=active_dataset.index)
    for column in active_dataset.columns:
        matching_rows |= (
            active_dataset[column]
            .astype("string")
            .str.contains(search_query, case=False, regex=False, na=False)
        )
    filtered_dataset = active_dataset.loc[matching_rows]

st.caption(
    f"Menampilkan {min(len(filtered_dataset), row_limit):,} dari "
    f"{len(filtered_dataset):,} baris yang cocok."
)
st.dataframe(
    filtered_dataset.head(row_limit),
    width="stretch",
    hide_index=True,
)

st.divider()
st.subheader("Unggah dataset baru")
st.write(
    "Pilih berkas CSV atau Excel XLSX. Dataset aktif tidak akan berubah "
    "sampai validasi berhasil dan Anda mengonfirmasi penyimpanan."
)

try:
    template_content = create_dataset_template(active_dataset.columns)
except Exception as exc:
    st.error("Template Excel gagal dibuat.")
    st.caption(f"Detail: {exc}")
else:
    st.download_button(
        "Unduh Template Excel",
        data=template_content,
        file_name="template_dataset_longsor.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="secondary",
        width="stretch",
        help="Template berisi nama kolom dataset aktif tanpa baris data.",
    )

uploaded_file = st.file_uploader(
    "Pilih berkas dataset",
    type=["csv", "xlsx"],
    help="Kolom dataset harus mencakup seluruh kolom wajib pada dataset penelitian.",
)

if uploaded_file is not None:
    st.caption(
        f"Berkas dipilih: **{uploaded_file.name}** · "
        f"{display_file_size(uploaded_file.size)}"
    )
    try:
        uploaded_dataset = read_uploaded_dataset(
            uploaded_file.name,
            uploaded_file.getvalue(),
        )
        validated_dataset, validation_errors, validation_warnings = validate_dataset(
            uploaded_dataset,
            active_dataset,
        )
    except Exception as exc:
        st.error(
            "Berkas gagal dibaca. Pastikan CSV memiliki pemisah dan encoding "
            "yang benar atau Excel berformat XLSX yang valid."
        )
        st.caption(f"Detail: {exc}")
    else:
        st.markdown("**Pratinjau data**")
        st.dataframe(
            validated_dataset.head(10),
            width="stretch",
            hide_index=True,
        )

        if validation_errors:
            st.error("Dataset belum dapat disimpan:")
            for error in validation_errors:
                st.markdown(f"- {error}")
        else:
            st.success(
                f"Validasi struktur berhasil: {len(validated_dataset):,} baris "
                f"dan {len(validated_dataset.columns):,} kolom."
            )

        for warning in validation_warnings:
            st.warning(warning)

        if not validation_errors and st.button(
            "Simpan Dataset",
            type="primary",
            width="stretch",
        ):
            try:
                save_active_dataset(uploaded_file.name, validated_dataset)
            except Exception as exc:
                st.error(
                    "Dataset gagal disimpan. Dataset aktif sebelumnya "
                    "tetap digunakan. Periksa koneksi Neon dan tabel "
                    "`active_dataset`."
                )
                st.caption(f"Detail: {exc}")
            else:
                st.session_state.dataset_success_message = (
                    f"Dataset “{uploaded_file.name}” berhasil disimpan ke "
                    "Neon dan sekarang menjadi dataset aktif."
                )
                st.rerun()