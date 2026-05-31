# 🛡️ FraudShield

Solução de **detecção de fraudes financeiras em tempo real** para o Neo Bank Finance.
Analisa cada transação no momento em que ocorre, classifica o risco, dispara
**alertas por e-mail e WhatsApp** ao cliente e ao time antifraude e alimenta
**dashboards executivos** (Python e Power BI).

> Projeto entregue pela **FinAnalytics** — Data. Strategy. Growth.

---

## ✨ Funcionalidades
- **Motor híbrido de ML**: RandomForest supervisionado + IsolationForest (anomalias/fraudes novas).
- **Scoring em tempo real** via API REST (FastAPI) ou simulador de stream.
- **Alertas automáticos** por e-mail (SMTP) e WhatsApp (Twilio) — modo `simulacao` ou `real`.
- **Gráficos comparativos** dos tipos de fraude mais detectados.
- **Modelo dimensional (star schema)** pronto para Power BI, com medidas DAX.
- Pronto para **deploy** (Docker) e **versionamento no GitHub** (CI incluso).

## 📊 Resultados do modelo (base creditcard, hold-out estratificado)
| Métrica | Valor |
|---|---|
| ROC-AUC | **0,96** |
| PR-AUC | **0,85** |
| Precisão | **0,98** |
| Recall | **0,66** |
| F1 | **0,79** |

> Precisão de 98% significa pouquíssimos falsos positivos — o time antifraude
> só é acionado quando o risco é real.

## 🗂️ Estrutura
```
Neo-Bank-Finance-FraudShield/
├── src/                  # código-fonte (pipeline, modelo, alertas, tempo real)
│   ├── data_loader.py    # carga das bases
│   ├── features.py       # engenharia de atributos + taxonomia de fraude
│   ├── model.py          # treino/score (RandomForest + IsolationForest)
│   ├── eda.py            # gráficos comparativos
│   ├── alerts.py         # e-mail (SMTP) + WhatsApp (Twilio)
│   ├── realtime_scoring.py  # API + simulador de stream
│   ├── export_powerbi.py # gera o star schema para Power BI
│   └── main.py           # CLI orquestrador
├── powerbi/              # modelo dimensional + medidas DAX + guia
├── reports/figures/      # gráficos gerados
├── data/raw/             # bases (não versionadas)
├── models/               # modelo treinado (não versionado)
├── tests/                # testes automatizados
├── docs/                 # documentação e deploy
├── Dockerfile · docker-compose.yml · .github/workflows/ci.yml
└── requirements.txt
```

## 🚀 Início rápido
```bash
# 1. Ambiente
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configuração
cp config/config.example.yaml config/config.yaml
cp .env.example .env            # preencha credenciais (opcional p/ alertas reais)

# 3. Pipeline completo (treino + gráficos + Power BI)
python -m src.main tudo

# 4. Demonstração de tempo real (alertas simulados)
python -m src.main stream

# 5. API REST
uvicorn src.realtime_scoring:criar_app --factory --reload
# POST http://localhost:8000/score
```

## 🔔 Alertas (e-mail + WhatsApp)
Em `config/config.yaml`, defina `alertas.modo`:
- `simulacao` — registra os alertas em log (para demonstração, sem credenciais).
- `real` — envia de fato via SMTP (e-mail) e Twilio (WhatsApp). Credenciais no `.env`.

## 📈 Power BI
Veja `powerbi/guia_powerbi.md` para reconstruir os dashboards interativos e
configurar o **monitoramento em tempo real** (streaming dataset / DirectQuery).

## 🐳 Deploy
```bash
docker compose up --build      # sobe a API de scoring na porta 8000
```

## 📄 Licença
Uso interno Neo Bank Finance / FinAnalytics. © 2026.
