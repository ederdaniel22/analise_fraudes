"""
Testa a API do FraudShield enviando transações de exemplo.

Pré-requisitos:
  1) A API precisa estar no ar, em outro terminal:
       uvicorn src.realtime_scoring:criar_app --factory
  2) Instale o cliente HTTP (uma única vez):
       python -m pip install requests

Uso:
  python testar_api.py                 # roda os 3 casos de exemplo
  python testar_api.py --url http://127.0.0.1:8000
"""
from __future__ import annotations
import argparse, json, sys

try:
    import requests
except ImportError:
    sys.exit("Faltou o pacote 'requests'. Rode:  python -m pip install requests")

# ---- Casos de teste (meta = dados de negócio; features = entrada do modelo) ----
CASOS = [
    {
        "nome": "Transferência alta de madrugada (suspeita)",
        "meta": {"TransactionID": "TX1001", "AccountID": "AC00321",
                 "TransactionAmount": 48750.00, "Channel": "Online",
                 "Location": "São Paulo", "Transaction_Type": "Transfer",
                 "Device_Type": "Desktop"},
        # valores extremos -> tende a acionar o detector de anomalia
        "features_extremas": True,
    },
    {
        "nome": "Compra normal no débito (legítima)",
        "meta": {"TransactionID": "TX1002", "AccountID": "AC00120",
                 "TransactionAmount": 89.90, "Channel": "POS",
                 "Location": "Curitiba", "Transaction_Type": "Debit",
                 "Device_Type": "POS"},
        "features_extremas": False,
    },
    {
        "nome": "Saque em ATM acima do padrão (suspeita)",
        "meta": {"TransactionID": "TX1003", "AccountID": "AC00999",
                 "TransactionAmount": 12500.00, "Channel": "ATM",
                 "Location": "Recife", "Transaction_Type": "Withdrawal",
                 "Device_Type": "ATM"},
        "features_extremas": True,
    },
]


def montar_features(extremas: bool) -> dict:
    """Gera o vetor de features esperado pelo modelo (V1..V28 + Amount).
    Em produção, viriam da transação real; aqui simulamos padrão normal vs anômalo."""
    import random
    cols = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
    if extremas:
        return {c: random.gauss(0, 6) for c in cols}      # longe do normal
    return {c: random.gauss(0, 1) for c in cols}          # dentro do normal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000", help="URL base da API")
    args = ap.parse_args()
    base = args.url.rstrip("/")

    # 1) checa se a API está no ar
    try:
        h = requests.get(f"{base}/health", timeout=5)
        print(f"✅ API no ar em {base}  (health: {h.json()})\n")
    except Exception as e:
        sys.exit(f"❌ Não consegui falar com a API em {base}.\n"
                 f"   Suba o servidor antes:  uvicorn src.realtime_scoring:criar_app --factory\n"
                 f"   Detalhe: {e}")

    # 2) envia cada caso
    for i, caso in enumerate(CASOS, 1):
        payload = {"features": montar_features(caso["features_extremas"]),
                   "meta": caso["meta"]}
        r = requests.post(f"{base}/score", json=payload, timeout=10)
        print("─" * 64)
        print(f"[{i}] {caso['nome']}")
        print(f"    Transação: {caso['meta']['TransactionID']}  |  "
              f"Valor: R$ {caso['meta']['TransactionAmount']:,.2f}  |  "
              f"Tipo: {caso['meta']['Transaction_Type']}")
        if r.status_code != 200:
            print(f"    ⚠️ Erro {r.status_code}: {r.text}")
            continue
        res = r.json()
        flag = "🚨 ALERTA DE FRAUDE" if res.get("alerta") else "✅ Transação liberada"
        print(f"    Score de fraude: {res.get('score_fraude', 0):.0%}  |  "
              f"Anomalia: {'sim' if res.get('anomalia') else 'não'}  |  "
              f"Tipo estimado: {res.get('tipo_fraude', 'N/A')}")
        print(f"    Resultado: {flag}")
        if res.get("alertas_enviados"):
            print(f"    Alertas disparados (simulação): {json.dumps(res['alertas_enviados'], ensure_ascii=False)}")
    print("─" * 64)
    print("\nDica: veja os alertas detalhados no terminal onde o uvicorn está rodando.")


if __name__ == "__main__":
    main()
