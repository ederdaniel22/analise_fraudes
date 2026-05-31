"""Orquestrador de linha de comando do FraudShield.

Uso:
  python -m src.main treinar       # treina o modelo e salva métricas
  python -m src.main graficos      # gera todos os gráficos
  python -m src.main powerbi       # exporta tabelas do modelo Power BI
  python -m src.main stream        # roda o simulador de tempo real
  python -m src.main tudo          # pipeline completo
"""
from __future__ import annotations
import sys, json, logging
from pathlib import Path
from .config import load_config
from . import data_loader as DL
from . import features as F
from . import model as M
from . import eda as E

log = logging.getLogger("fraudshield.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
ROOT = Path(__file__).resolve().parents[1]

def treinar(cfg):
    log.info("Carregando base rotulada (creditcard)...")
    cc = DL.load_creditcard(cfg["dados"]["creditcard"])
    X, y, target = F.features_creditcard(cc)
    # Subamostragem da classe majoritária para treino eficiente em memória
    # (mantém todas as fraudes + amostra de legítimas). Avaliação em hold-out estratificado.
    idx_f = y[y == 1].index
    n_leg = min(60000, int((y == 0).sum()))
    idx_l = y[y == 0].sample(n_leg, random_state=42).index
    sel = idx_f.union(idx_l)
    Xs, ys = X.loc[sel], y.loc[sel]
    log.info(f"Treinando modelo híbrido | base total {len(cc):,} | amostra treino {len(Xs):,} (fraudes={int(ys.sum())})")
    metrics = M.treinar(Xs, ys, limiar=cfg["modelo"]["limiar_alerta"],
                         salvar_em=cfg["modelo"]["caminho"])
    log.info(f"Métricas: ROC-AUC={metrics['roc_auc']} | PR-AUC={metrics['pr_auc']} "
             f"| Recall={metrics['recall']} | Precision={metrics['precision']}")
    return metrics

def graficos(cfg):
    log.info("Gerando gráficos...")
    bank = F.enriquecer_bank(DL.load_bank_transactions(cfg["dados"]["bank_transactions"]))
    cc = DL.load_creditcard(cfg["dados"]["creditcard"]); _,_,target = F.features_creditcard(cc)
    mpath = Path(cfg["modelo"]["caminho"]).with_suffix(".metrics.json")
    metrics = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else treinar(cfg)
    saidas = [
        E.grafico_tipos_fraude(bank), E.grafico_taxa_por_canal(bank),
        E.grafico_valor_distribuicao(cc, target), E.grafico_fraude_por_hora(bank),
        E.grafico_top_estados(bank), E.grafico_importancia(metrics),
        E.grafico_matriz_confusao(metrics), E.grafico_economia(bank),
    ]
    for s in saidas: log.info(f"  gerado: {s.name}")
    return saidas

def powerbi(cfg):
    from .export_powerbi import exportar
    return exportar(cfg)

def stream(cfg):
    from .realtime_scoring import simular_stream
    return simular_stream(n=25, intervalo=0.05)

def main():
    cfg = load_config()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tudo"
    if cmd == "treinar": treinar(cfg)
    elif cmd == "graficos": graficos(cfg)
    elif cmd == "powerbi": powerbi(cfg)
    elif cmd == "stream": stream(cfg)
    else:
        treinar(cfg); graficos(cfg); powerbi(cfg)
    log.info("Concluído.")

if __name__ == "__main__":
    main()
