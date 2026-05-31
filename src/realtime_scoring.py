"""Motor de scoring em tempo real.

Dois modos de operação:
  1) API REST (FastAPI) -> POST /score recebe uma transação e devolve o veredito.
  2) Simulador de stream -> processa transações em fluxo e dispara alertas.
"""
from __future__ import annotations
import logging, time, random
from pathlib import Path
from .config import load_config
from . import model as M
from . import alerts as A
from .features import classificar_tipo_fraude

log = logging.getLogger("fraudshield.realtime")
ROOT = Path(__file__).resolve().parents[1]

# Schema da transação para a API (nível de módulo: pydantic resolve o tipo corretamente).
try:
    from pydantic import BaseModel
    class Transacao(BaseModel):
        features: dict
        meta: dict = {}
except ImportError:          # pydantic só é necessário para a API REST
    Transacao = None

def _carregar_bundle(cfg):
    caminho = Path(cfg["modelo"]["caminho"])
    if not caminho.is_absolute():
        caminho = ROOT / caminho           # resolve a partir da raiz do projeto
    if not caminho.exists():
        raise FileNotFoundError(
            f"Modelo não encontrado em {caminho}. Rode primeiro: python -m src.main treinar")
    return M.carregar(str(caminho))

def avaliar_transacao(tx: dict, cfg=None, bundle=None) -> dict:
    cfg = cfg or load_config()
    bundle = bundle or _carregar_bundle(cfg)
    res = M.score_transacao(bundle, tx["features"])
    res["tipo_fraude"] = classificar_tipo_fraude(tx.get("meta", {}))
    if res["alerta"]:
        envio = A.disparar_alertas(cfg["alertas"], tx.get("meta", tx), res)
        res["alertas_enviados"] = envio
    return res

# ---------- Simulador de stream (demo offline, sem servidor) ----------
def simular_stream(n=20, intervalo=0.2):
    """Gera n transações sintéticas e processa em 'tempo real' para demonstração."""
    cfg = load_config(); bundle = _carregar_bundle(cfg)
    cols = bundle["cols"]
    disparados = 0
    for i in range(n):
        feats = {c: random.gauss(0, 1) for c in cols}
        if random.random() < 0.25:  # injeta padrão anômalo
            for c in list(cols)[:5]: feats[c] = random.gauss(0, 6)
        tx = {"meta": {"TransactionID": f"TX{i:06d}", "AccountID": f"AC{random.randint(1,999):05d}",
                       "TransactionAmount": round(random.uniform(10, 90000), 2),
                       "Channel": random.choice(["ATM","Online","POS","Mobile"]),
                       "Location": random.choice(["São Paulo","Rio","Recife","Curitiba"]),
                       "Transaction_Type": random.choice(["Transfer","Debit","Withdrawal"]),
                       "Device_Type": random.choice(["ATM","Mobile","Desktop"])},
              "features": feats}
        res = avaliar_transacao(tx, cfg, bundle)
        flag = "🚨 ALERTA" if res["alerta"] else "ok"
        log.info(f"{tx['meta']['TransactionID']} score={res['score_fraude']:.0%} {flag}")
        if res["alerta"]: disparados += 1
        time.sleep(intervalo)
    log.info(f"Stream finalizado: {disparados}/{n} alertas disparados.")
    return disparados

# ---------- API REST (opcional) ----------
def criar_app():
    from fastapi import FastAPI
    cfg = load_config(); bundle = _carregar_bundle(cfg)
    app = FastAPI(title="FraudShield API")

    @app.get("/")
    def home():
        return {"servico": "FraudShield API",
                "status": "no ar",
                "teste_interativo": "/docs",
                "endpoints": ["/health", "/score (POST)"]}

    @app.get("/health")
    def health(): return {"status": "ok"}

    @app.post("/score")
    def score(tx: Transacao):
        return avaliar_transacao(tx.model_dump(), cfg, bundle)
    return app
