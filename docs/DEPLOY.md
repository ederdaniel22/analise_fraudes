# Guia de Deploy — FraudShield

## Ambientes
| Ambiente | Uso | Branch |
|---|---|---|
| dev | desenvolvimento local | feature/* |
| homologação | validação com dados mascarados | develop |
| produção | operação 24/7 | main |

## Versionamento (GitHub)
```bash
git init && git add . && git commit -m "feat: FraudShield MVP"
git branch -M main
git remote add origin git@github.com:neobank/fraudshield.git
git push -u origin main
```
Fluxo: `feature/*` → PR → `develop` (homologação) → PR → `main` (produção).
CI roda `pytest` a cada push/PR (`.github/workflows/ci.yml`).

## Deploy com Docker
```bash
docker compose up --build -d        # API de scoring em :8000
curl localhost:8000/health
```

## Operação em tempo real
1. O barramento de transações do banco publica eventos numa fila (Kafka/RabbitMQ).
2. O serviço FraudShield consome, faz `score_transacao` e grava o resultado.
3. Transações com `alerta=True` disparam e-mail + WhatsApp e marcam para bloqueio.
4. Power BI lê os scores (streaming dataset / DirectQuery) para o painel ao vivo.

## Segurança e compliance
- Segredos em variáveis de ambiente (`.env`) — nunca no código.
- Dados sensíveis fora do versionamento (`.gitignore`).
- Trilha de auditoria: todo alerta registrado com timestamp e score.
- LGPD: dados de cliente mascarados em ambientes não-produtivos.

## Retreino do modelo
Agende `python -m src.main treinar` (cron/Airflow) semanalmente com os rótulos
confirmados pelos analistas (feedback loop) para manter a acurácia.
