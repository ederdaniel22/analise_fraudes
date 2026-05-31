"""Treino e persistência do motor de detecção de fraude.

Estratégia híbrida:
  - Supervisionado: RandomForest sobre a base rotulada (creditcard) -> score de probabilidade.
  - Não-supervisionado: IsolationForest para anomalias sem rótulo (cobre fraudes novas).
"""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (roc_auc_score, average_precision_score,
                             precision_recall_fscore_support, confusion_matrix)

ROOT = Path(__file__).resolve().parents[1]

def treinar(X, y, limiar: float = 0.80, salvar_em: str | None = None) -> dict:
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=42)
    scaler = StandardScaler().fit(Xtr)
    Xtr_s = scaler.transform(Xtr).astype('float32')
    Xte_s = scaler.transform(Xte).astype('float32')

    clf = RandomForestClassifier(
        n_estimators=120, max_depth=16, n_jobs=2, max_samples=0.4,
        class_weight="balanced", random_state=42)
    clf.fit(Xtr_s.astype("float32"), ytr)

    iso = IsolationForest(n_estimators=100, max_samples=20000,
                          contamination=float(y.mean()),
                          random_state=42, n_jobs=2)
    iso.fit(Xtr_s[ytr.values == 0].astype("float32"))  # aprende o "normal"

    proba = clf.predict_proba(Xte_s)[:, 1]
    pred = (proba >= limiar).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(yte, pred, average="binary", zero_division=0)
    metrics = {
        "roc_auc": round(float(roc_auc_score(yte, proba)), 4),
        "pr_auc": round(float(average_precision_score(yte, proba)), 4),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "limiar": limiar,
        "n_treino": int(len(ytr)), "n_teste": int(len(yte)),
        "taxa_fraude": round(float(y.mean()), 5),
        "matriz_confusao": confusion_matrix(yte, pred).tolist(),
        "top_features": _importancias(clf, X.columns),
    }
    if salvar_em:
        Path(salvar_em).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"clf": clf, "iso": iso, "scaler": scaler,
                     "cols": list(X.columns), "limiar": limiar}, salvar_em)
        with open(Path(salvar_em).with_suffix(".metrics.json"), "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    return metrics

def _importancias(clf, cols, k=10):
    idx = np.argsort(clf.feature_importances_)[::-1][:k]
    return [{"feature": str(cols[i]), "importancia": round(float(clf.feature_importances_[i]), 4)} for i in idx]

def carregar(caminho: str):
    return joblib.load(caminho)

def score_transacao(bundle, registro: dict) -> dict:
    """Score em tempo real de uma transação (dict de features)."""
    import pandas as pd
    # Reindexa para as colunas do modelo: campos ausentes viram 0, extras são ignorados.
    # Torna a API tolerante a payloads parciais (ex.: sem a coluna 'Time').
    x = pd.DataFrame([registro]).reindex(columns=bundle["cols"], fill_value=0)
    xs = bundle["scaler"].transform(x)
    proba = float(bundle["clf"].predict_proba(xs)[:, 1][0])
    anomalia = bool(bundle["iso"].predict(xs)[0] == -1)
    return {"score_fraude": round(proba, 4),
            "anomalia": anomalia,
            "alerta": proba >= bundle["limiar"] or anomalia}
