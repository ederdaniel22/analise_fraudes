"""Testes automatizados do pipeline FraudShield."""
import numpy as np, pandas as pd
from src import features as F, model as M, alerts as A

def _dataset(n=2000, p=0.05, seed=0):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < p).astype(int)
    X = pd.DataFrame(rng.normal(size=(n, 6)), columns=[f"V{i}" for i in range(6)])
    X.loc[y == 1] += 3  # injeta sinal de fraude
    X["Class"] = y
    return X

def test_features_split():
    df = _dataset()
    X, y, target = F.features_creditcard(df)
    assert target == "Class" and "Class" not in X.columns and len(y) == len(X)

def test_treino_e_score():
    df = _dataset()
    X, y, _ = F.features_creditcard(df)
    m = M.treinar(X, y, limiar=0.5, salvar_em="models/_test_model.joblib")
    assert m["roc_auc"] > 0.8          # sinal detectável
    bundle = M.carregar("models/_test_model.joblib")
    reg = {c: 5.0 for c in bundle["cols"]}   # padrão claramente fraudulento
    res = M.score_transacao(bundle, reg)
    assert 0.0 <= res["score_fraude"] <= 1.0 and "alerta" in res

def test_classificar_tipo_fraude():
    assert F.classificar_tipo_fraude({"Transaction_Type": "Transfer"}) == "Golpe de Transferência/PIX"
    assert F.classificar_tipo_fraude({"Transaction_Type": "Withdrawal"}) == "Fraude em ATM/Saque"

def test_alertas_simulacao():
    cfg = {"modo": "simulacao",
           "email": {"destinatarios_analistas": ["a@b.com"], "remetente": "x@y.com"},
           "whatsapp": {"numeros_analistas": ["whatsapp:+550000"]}}
    tx = {"TransactionID": "TX1", "TransactionAmount": 999}
    res = {"score_fraude": 0.95, "anomalia": True, "tipo_fraude": "Fraude de Cartão (CNP)"}
    out = A.disparar_alertas(cfg, tx, res)
    assert out["email_analistas"] and out["whatsapp_analistas"]
