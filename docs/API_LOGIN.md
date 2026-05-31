# Sistema de Login e API Web - FraudShield

## 📋 Descrição

Este sistema oferece uma interface web completa com autenticação JWT para:

- **Login e Registro** de usuários
- **Dashboard** com visualização de dados de clientes
- **Análise de Transações** em tempo real
- **Gestão de Perfil** de usuário
- **API REST** para integração

## 🚀 Como Usar

### 1. Instalando as Dependências

Todas as dependências já estão listadas em `requirements.txt`. Se ainda não instalou, execute:

```bash
pip install -r requirements.txt
```

### 2. Iniciando a API

Existem duas formas de iniciar a API:

**Opção A: Usando o script principal**

```bash
python main_api.py
```

**Opção B: Usando uvicorn diretamente**

```bash
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em: **http://localhost:8000**

### 3. Acessando o Dashboard

Abra seu navegador e vá para: **http://localhost:8000**

Você verá a página de login.

## 👤 Credenciais de Teste

O sistema vem com 3 usuários pré-configurados para teste:

| Email                | Senha       | Função             |
| -------------------- | ----------- | ------------------ |
| admin@neobank.com    | admin123    | Administrador      |
| analista@neobank.com | analista123 | Analista de Fraude |
| cliente@neobank.com  | cliente123  | Cliente            |

## 🎯 Funcionalidades

### Dashboard

- Visualização de estatísticas gerais
- Total de clientes
- Fraudes detectadas
- Valores de transações

### Gestão de Clientes

- Lista de clientes cadastrados
- Informações de transações
- Status de segurança (Fraude/Seguro)

### Análise de Transações

- Formulário para análise manual
- Score de risco de fraude
- Classificação de tipo de fraude
- Alertas em tempo real

### Perfil de Usuário

- Visualização de dados pessoais
- Função e status

## 🔐 Autenticação

O sistema usa **JWT (JSON Web Tokens)** para autenticação:

1. Usuário faz login com email e senha
2. API retorna um token JWT
3. Token é armazenado no localStorage
4. Token é enviado em toda requisição via header `token`

### Headers de Autenticação

```
token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 📡 Endpoints da API

### Autenticação

**POST /api/login**

```json
{
  "email": "usuario@neobank.com",
  "senha": "senha123"
}
```

**POST /api/registrar**

```json
{
  "email": "novo@neobank.com",
  "nome": "Novo Usuário",
  "senha": "senha123"
}
```

**GET /api/perfil**

- Headers: `token: <seu_token>`

### Clientes

**GET /api/clientes**

- Headers: `token: <seu_token>`
- Query: `?limite=100`

**GET /api/clientes/{cliente_id}**

- Headers: `token: <seu_token>`

**GET /api/clientes/estatisticas/resumo**

- Headers: `token: <seu_token>`

### Análise

**POST /api/analisar-transacao**

- Headers: `token: <seu_token>`
- Body:

```json
{
  "features": {
    "V1": 1.5,
    "V2": -0.3,
    "Amount": 150.0,
    "Time": 1234567890
  },
  "meta": {
    "Channel": "Online",
    "Transaction_Type": "Transfer",
    "Location": "São Paulo"
  }
}
```

### Health Check

**GET /health**

- Sem autenticação necessária

## 📁 Estrutura de Arquivos

```
src/
├── api.py              # API FastAPI principal
├── auth.py             # Autenticação e JWT
├── dashboard.html      # Interface web (HTML/CSS/JS)
├── main.py             # Orquestrador CLI
├── config.py           # Carregamento de configuração
├── data_loader.py      # Carregamento de dados
├── features.py         # Engenharia de features
├── model.py            # Modelo de ML
├── realtime_scoring.py # Scoring em tempo real
├── alerts.py           # Sistema de alertas
├── eda.py              # Análise exploratória
└── export_powerbi.py   # Exportação para PowerBI

main_api.py            # Script para iniciar a API
```

## 🔧 Configuração

### Variáveis de Ambiente

Você pode configurar a chave secreta do JWT:

```bash
export SECRET_KEY="sua-chave-secreta-muito-segura"
```

### Arquivo config.yaml

Configure os parâmetros do modelo em `config/config.yaml`:

```yaml
modelo:
  caminho: "models/fraud_model.joblib"
  limiar_alerta: 0.80
  limiar_revisao: 0.50
```

## 🔒 Segurança

**Importante para Produção:**

1. Altere a `SECRET_KEY` em `src/auth.py`
2. Use um banco de dados real em vez do dicionário em memória
3. Configure HTTPS/SSL
4. Implemente rate limiting
5. Use senhas com hash seguro (já implementado com bcrypt)
6. Configure CORS apropriadamente

## 📊 Integração com Modelo de ML

O sistema integra automaticamente:

- Carregamento do modelo treinado
- Scoring de transações em tempo real
- Cálculo de features automático
- Geração de alertas

## 🧪 Testando a API

### Com cURL

```bash
# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@neobank.com","senha":"admin123"}'

# Obter clientes (substitua TOKEN)
curl http://localhost:8000/api/clientes \
  -H "token: TOKEN"
```

### Com Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8000/api/login',
    json={'email': 'admin@neobank.com', 'senha': 'admin123'}
)
token = response.json()['access_token']

# Listar clientes
response = requests.get(
    'http://localhost:8000/api/clientes',
    headers={'token': token}
)
print(response.json())
```

## 📝 Logs

A API gera logs detalhados em tempo real. Procure por mensagens com:

- `[INFO]` - Informações gerais
- `[ERROR]` - Erros
- `[DEBUG]` - Informações de debug

## 🆘 Troubleshooting

### "Porta 8000 já em uso"

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

### "ModuleNotFoundError: No module named 'fastapi'"

```bash
pip install -r requirements.txt
```

### Token expirado

- Faça login novamente para obter um novo token
- Token expira após 60 minutos por padrão

## 📞 Suporte

Para mais informações sobre o modelo de detecção de fraudes, consulte:

- [README.md](../README.md) - Documentação principal
- [DEPLOY.md](../docs/DEPLOY.md) - Guia de deploy

---

**Versão:** 1.0.0  
**Última atualização:** Maio 2026
