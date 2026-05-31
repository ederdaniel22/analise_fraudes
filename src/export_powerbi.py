"""Exporta o modelo dimensional (star schema) para o Power BI em CSV.

Gera: fato_transacoes, dim_tempo, dim_cliente, dim_canal, dim_tipo_fraude,
dim_geografia -> pasta powerbi/dados_modelo/
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from .config import load_config
from . import data_loader as DL
from . import features as F

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi" / "dados_modelo"

def exportar(cfg=None):
    cfg = cfg or load_config()
    OUT.mkdir(parents=True, exist_ok=True)
    bank = F.enriquecer_bank(DL.load_bank_transactions(cfg["dados"]["bank_transactions"]))

    # ---- dim_tempo ----
    dt = bank[["Transaction_DateTime"]].dropna().copy()
    dt["DataKey"] = dt["Transaction_DateTime"].dt.strftime("%Y%m%d").astype(int)
    dim_tempo = dt.drop_duplicates("DataKey").copy()
    dim_tempo["Data"] = dim_tempo["Transaction_DateTime"].dt.date
    dim_tempo["Ano"] = dim_tempo["Transaction_DateTime"].dt.year
    dim_tempo["Mes"] = dim_tempo["Transaction_DateTime"].dt.month
    dim_tempo["NomeMes"] = dim_tempo["Transaction_DateTime"].dt.strftime("%b")
    dim_tempo["Dia"] = dim_tempo["Transaction_DateTime"].dt.day
    dim_tempo["DiaSemana"] = dim_tempo["Transaction_DateTime"].dt.day_name()
    dim_tempo = dim_tempo[["DataKey","Data","Ano","Mes","NomeMes","Dia","DiaSemana"]]

    # ---- dim_canal ----
    dim_canal = pd.DataFrame({"Canal": sorted(bank["Device_Type"].unique())})
    dim_canal.insert(0,"CanalKey",range(1,len(dim_canal)+1))
    map_canal = dict(zip(dim_canal["Canal"],dim_canal["CanalKey"]))

    # ---- dim_tipo_fraude ----
    dim_tf = pd.DataFrame({"TipoFraude": F.TIPOS_FRAUDE})
    dim_tf.insert(0,"TipoFraudeKey",range(1,len(dim_tf)+1))
    map_tf = dict(zip(dim_tf["TipoFraude"],dim_tf["TipoFraudeKey"]))

    # ---- dim_geografia ----
    dim_geo = bank[["State","City"]].drop_duplicates().reset_index(drop=True)
    dim_geo.insert(0,"GeoKey",range(1,len(dim_geo)+1))
    map_geo = {(r.State,r.City):r.GeoKey for r in dim_geo.itertuples()}

    # ---- dim_cliente ----
    dim_cli = bank[["Customer_ID","Gender","Age","Account_Type"]].drop_duplicates("Customer_ID").reset_index(drop=True)

    # ---- fato_transacoes ----
    fato = pd.DataFrame({
        "TransactionID": bank["Transaction_ID"],
        "Customer_ID": bank["Customer_ID"],
        "DataKey": bank["Transaction_DateTime"].dt.strftime("%Y%m%d").astype("Int64"),
        "CanalKey": bank["Device_Type"].map(map_canal),
        "TipoFraudeKey": bank["Tipo_Fraude"].map(map_tf),
        "GeoKey": [map_geo.get((s,c)) for s,c in zip(bank["State"],bank["City"])],
        "Valor": bank["Transaction_Amount"],
        "Saldo": bank["Account_Balance"],
        "TransactionType": bank["Transaction_Type"],
        "MerchantCategory": bank["Merchant_Category"],
        "Hora": bank["Hora"],
        "Is_Fraud": bank["Is_Fraud"],
    })

    arquivos = {
        "fato_transacoes.csv": fato,
        "dim_tempo.csv": dim_tempo,
        "dim_cliente.csv": dim_cli,
        "dim_canal.csv": dim_canal,
        "dim_tipo_fraude.csv": dim_tf,
        "dim_geografia.csv": dim_geo,
    }
    for nome, d in arquivos.items():
        d.to_csv(OUT / nome, index=False, encoding="utf-8-sig")
    return {k: len(v) for k, v in arquivos.items()}
