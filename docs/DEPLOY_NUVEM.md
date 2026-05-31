# Publicação na Nuvem — FraudShield (Neo Bank Finance)

## O que é cada parte
- **API (Python/FastAPI + modelo ML)** → precisa de um host de **container** (não serverless).
- **Frontend (HTML de login/dashboard)** → pode ir junto da API (já é servido por ela) ou separado no Vercel.

## Por que NÃO usar Vercel para a API
O Vercel roda funções **serverless** com limite de tamanho (~250 MB descompactado) e sem processo
persistente. Com `scikit-learn` + `pandas` + `numpy` + o modelo, o pacote estoura o limite e o
cold start fica ruim. Use o Vercel **só para o frontend**, apontando para a API publicada em outro host.

## Pré-requisitos
1. Modelo treinado presente: `models/fraud_model.joblib` (rode `python -m src.main treinar`).
2. Conta no GitHub e o projeto versionado (`git init`, `git push`).
3. **Importante:** `models/*.joblib` e os CSVs estão no `.gitignore`. Para deploy baseado em Git
   (Render/Railway), inclua o que o runtime precisa, à força:
   ```bash
   git add -f models/fraud_model.joblib data/raw/Bank_Transaction_Fraud_Detection.csv
   git commit -m "deploy: incluir modelo e dados de runtime"
   git push
   ```
   (Fly.io e Cloud Run enviam os arquivos locais e dispensam esse passo.)

## Variável de ambiente obrigatória em produção
- `SECRET_KEY` → chave de assinatura dos tokens JWT. Defina um valor forte
  (no Render o `render.yaml` já gera automaticamente).

---

## Opção A — Render (recomendado, tem plano grátis)
1. Suba o projeto para um repositório no GitHub.
2. Em https://render.com → **New → Blueprint** e selecione o repositório
   (ele lê o `render.yaml` já incluso e cria o serviço Docker).
3. Aguarde o build. A URL pública sai como `https://fraudshield-api.onrender.com`.
4. Acesse `/` (dashboard) e `/docs` (API). Login de teste: `admin@neobank.com` / `admin123`.

## Opção B — Railway
1. https://railway.app → **New Project → Deploy from GitHub repo**.
2. Railway detecta o `Dockerfile` automaticamente.
3. Em **Variables**, adicione `SECRET_KEY`. Railway injeta `PORT` sozinho.
4. **Settings → Networking → Generate Domain** para obter a URL pública.

## Opção C — Fly.io (envia os arquivos locais; não precisa commitar modelo/CSV)
```bash
# instale o flyctl, depois:
fly launch --no-deploy        # detecta o Dockerfile e cria fly.toml
fly secrets set SECRET_KEY="troque-por-uma-chave-forte"
fly deploy
```
A URL sai como `https://<seu-app>.fly.dev`.

## Opção D — Google Cloud Run (envia o diretório local)
```bash
gcloud run deploy fraudshield-api \
  --source . \
  --region southamerica-east1 \
  --allow-unauthenticated \
  --set-env-vars SECRET_KEY="troque-por-uma-chave-forte"
```
O Cloud Run faz o build da imagem e devolve uma URL `https://...run.app`.

---

## Opção E — Frontend no Vercel (apontando para a API publicada)
Use isto só se quiser o frontend separado da API.
1. Publique a API primeiro (Opção A–D) e copie a URL dela.
2. Nos arquivos `SISTEMA_LOGIN.html` e `src/dashboard.html`, troque
   `http://localhost:8000` pela URL pública da API.
3. Na API, libere o domínio do Vercel no CORS (`allow_origins`) em `src/api.py`.
4. Em https://vercel.com → **Add New → Project**, selecione o repositório.
   O `vercel.json` já roteia `/` para a tela de login.

## Dica de custo
Para um piloto/demonstração, **Render Free** ou **Fly.io** resolvem sem custo.
Para produção 24/7 com baixa latência, prefira **Cloud Run** ou um plano pago do Render/Railway.
