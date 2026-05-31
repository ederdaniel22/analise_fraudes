"""Engenharia de atributos e taxonomia de tipos de fraude."""
from __future__ import annotations
import pandas as pd

# Taxonomia de tipos de fraude usada nos dashboards e relatórios executivos.
TIPOS_FRAUDE = [
    "Fraude de Cartão (CNP)",      # card-not-present / e-commerce
    "Apropriação de Conta (ATO)",  # account takeover
    "Golpe de Transferência/PIX",  # social engineering transfer
    "Fraude em ATM/Saque",         # skimming / saque
    "Fraude de Pagamento de Conta",# boleto/bill fraud
]

def classificar_tipo_fraude(row) -> str:
    """Mapeia uma transação suspeita para um tipo de fraude (regras de negócio)."""
    canal = str(row.get("Device_Type", "")).lower()
    ttype = str(row.get("Transaction_Type", "")).lower()
    if ttype == "transfer":
        return "Golpe de Transferência/PIX"
    if ttype == "withdrawal" or canal == "atm":
        return "Fraude em ATM/Saque"
    if ttype == "bill payment":
        return "Fraude de Pagamento de Conta"
    if canal in ("desktop", "mobile") and ttype in ("debit", "credit"):
        return "Fraude de Cartão (CNP)"
    return "Apropriação de Conta (ATO)"

def features_creditcard(df: pd.DataFrame):
    """Separa X, y da base rotulada."""
    target = "Class" if "Class" in df.columns else "Target"
    X = df.drop(columns=[target])
    y = df[target].astype(int)
    return X, y, target

def enriquecer_bank(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona hora, faixa de valor e tipo de fraude estimado para análise."""
    df = df.copy()
    if "Transaction_DateTime" in df.columns:
        df["Hora"] = df["Transaction_DateTime"].dt.hour
    df["Faixa_Valor"] = pd.cut(df["Transaction_Amount"],
        bins=[-1, 1000, 10000, 50000, 1e12],
        labels=["Baixo", "Médio", "Alto", "Muito Alto"])
    df["Tipo_Fraude"] = df.apply(classificar_tipo_fraude, axis=1)
    return df
