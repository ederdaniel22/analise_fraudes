"""Carga e padronização das bases de transações do Neo Bank Finance."""
from __future__ import annotations
import pandas as pd
from pathlib import Path

def load_bank_transactions(path: str) -> pd.DataFrame:
    """Base transacional rica (segmentação: canal, geografia, categoria, dispositivo)."""
    df = pd.read_csv(path)
    df["Transaction_DateTime"] = pd.to_datetime(
        df["Transaction_Date"] + " " + df["Transaction_Time"],
        format="%d-%m-%Y %H:%M:%S", errors="coerce")
    return df

def load_creditcard(path: str) -> pd.DataFrame:
    """Base rotulada (V1..V28 PCA + Amount + Class). Sinal real de fraude."""
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    for c in df.columns:
        if df[c].dtype == "float64":
            df[c] = df[c].astype("float32")
    return df

def load_transferencias(path: str) -> pd.DataFrame:
    """Mesma base creditcard com nomes de negócio em PT-BR (Target = fraude)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().strip('"') for c in df.columns]
    return df
