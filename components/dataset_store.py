from __future__ import annotations

import hashlib
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

from components.auth import get_engine

APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"
ACTIVE_DATASET_PATH = DATA_DIR / "dataset_aktif.csv"
INITIAL_DATASET_PATH = DATA_DIR / "Tanah Longsor.xls"


@st.cache_data(ttl=60, show_spinner=False)
def _load_active_dataset_record() -> tuple[str, str] | None:
    query = text(
        "SELECT file_name, csv_content FROM active_dataset WHERE id = :dataset_id"
    )
    with get_engine().connect() as connection:
        row = connection.execute(query, {"dataset_id": 1}).fetchone()
    if row is None:
        return None
    return str(row[0]), str(row[1])

@st.cache_data(show_spinner=False)
def _load_local_dataset(path: str, modified_at: float) -> pd.DataFrame:
    del modified_at
    dataset_path = Path(path)
    if dataset_path.suffix.casefold() == ".csv":
        return pd.read_csv(dataset_path, encoding="utf-8-sig", low_memory=False)
    return pd.read_excel(dataset_path, engine="xlrd")

def load_active_dataset() -> tuple[str, pd.DataFrame, bool, str]:
    record = _load_active_dataset_record()
    if record is not None:
        file_name, csv_content = record
        dataset = pd.read_csv(StringIO(csv_content), low_memory=False)
        version = hashlib.sha256(csv_content.encode("utf-8")).hexdigest()
        return file_name, dataset, True, version

    if ACTIVE_DATASET_PATH.is_file():
        dataset_path = ACTIVE_DATASET_PATH
    elif INITIAL_DATASET_PATH.is_file():
        dataset_path = INITIAL_DATASET_PATH
    else:
        raise FileNotFoundError("Dataset tanah longsor tidak ditemukan.")

    dataset = _load_local_dataset(
        str(dataset_path),
        dataset_path.stat().st_mtime,
    )
    version = f"{dataset_path.stat().st_mtime_ns}:{dataset_path.stat().st_size}"
    return dataset_path.name, dataset, False, version

def save_active_dataset(file_name: str, dataset: pd.DataFrame) -> None:
    query = text(
        """
        INSERT INTO active_dataset (id, file_name, csv_content, updated_at)
        VALUES (:dataset_id, :file_name, :csv_content, now())
        ON CONFLICT (id) DO UPDATE SET
            file_name = EXCLUDED.file_name,
            csv_content = EXCLUDED.csv_content,
            updated_at = now()
        """
    )
    with get_engine().begin() as connection:
        connection.execute(
            query,
            {
                "dataset_id": 1,
                "file_name": file_name,
                "csv_content": dataset.to_csv(index=False),
            },
        )
    _load_active_dataset_record.clear()
    _load_local_dataset.clear()