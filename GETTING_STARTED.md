# 🚀 Guia de Início Rápido - Sistema de Login & API

## ⚡ Início Rápido (2 minutos)

### 1. Instale as dependências

```bash
pip install -r requirements.txt
```

### 2. Inicie o servidor API

**No Windows:**

```cmd
iniciar_api.bat
```

**No Linux/Mac:**

```bash
bash iniciar_api.sh
```

**Ou manualmente:**

```bash
python main_api.py
```

### 3. Abra seu navegador

```
http://localhost:8000
```

### 4. Faça login com as credenciais de teste

| Email                | Senha       |
| -------------------- | ----------- |
| admin@neobank.com    | admin123    |
| analista@neobank.com | analista123 |
| cliente@neobank.com  | cliente123  |

---

## 📱 Interface Web

### Dashboard

- **Estatísticas em tempo real** - Total de clientes, fraudes detectadas, valores
- **Gráficos atualizados** - Visualize os dados no painel

### Gestão de Clientes

- **Lista completa** de clientes cadastrados
- **Informações detalhadas** de transações
- **Status de segurança** (Fraude ou Seguro)

### Análise de Transações

- **Formulário intuitivo** para análise manual
- **Score de risco** de fraude em tempo real
- **Classificação automática** de tipo de fraude
- **Alertas** quando suspeita é detectada

### Perfil do Usuário

- **Dados pessoais** seguros
- **Função e permissões**

---

## 🔌 API REST

### Base URL

```
http://localhost:8000
```

### Autenticação

Use o header `token` em todas as requisições após fazer login:

```bash
curl http://localhost:8000/api/clientes \
  -H "token: SEU_TOKEN_JWT"
```

### Exemplos de Uso

#### Login

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@neobank.com",
    "senha": "admin123"
  }'
```

**Resposta:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "usuario": {
    "email": "admin@neobank.com",
    "nome": "Administrador",
    "role": "admin"
  }
}
```

#### Obter Clientes

```bash
curl http://localhost:8000/api/clientes?limite=50 \
  -H "token: SEU_TOKEN"
```

#### Analisar Transação

```bash
curl -X POST http://localhost:8000/api/analisar-transacao \
  -H "Content-Type: application/json" \
  -H "token: SEU_TOKEN" \
  -d '{
    "features": {
      "V1": 1.5,
      "V2": -0.3,
      "Amount": 150.00,
      "Time": 1234567890
    },
    "meta": {
      "Channel": "Online",
      "Transaction_Type": "Transfer",
      "Location": "São Paulo"
    }
  }'
```

---

## 📚 Documentação Completa

Para documentação detalhada, consulte:

- [docs/API_LOGIN.md](docs/API_LOGIN.md) - Guia completo da API e autenticação

---

## 🛠️ Arquivos Criados/Modificados

### Novos Arquivos

- `src/auth.py` - Sistema de autenticação JWT
- `src/api.py` - API FastAPI completa
- `src/dashboard.html` - Interface web (HTML5 + Bootstrap)
- `main_api.py` - Script para iniciar o servidor
- `iniciar_api.bat` - Script Windows
- `iniciar_api.sh` - Script Linux/Mac
- `docs/API_LOGIN.md` - Documentação completa

### Arquivos Modificados

- `requirements.txt` - Adicionadas dependências para JWT e FastAPI

---

## 🔐 Segurança

### Desenvolvimento

Para desenvolvimento local, as credenciais padrão são suficientes.

### Produção

⚠️ **IMPORTANTE**: Antes de fazer deploy em produção:

1. **Altere a SECRET_KEY** em `src/auth.py`
2. **Use um banco de dados real** em vez de dicionário em memória
3. **Configure HTTPS/SSL** no servidor
4. **Implemente rate limiting** e proteção contra brute force
5. **Configure CORS** adequadamente
6. **Use variáveis de ambiente** para dados sensíveis

Exemplo:

```bash
export SECRET_KEY="sua-chave-muito-segura-aleatorios-caracteres"
export PASSWORD_SALT="seu-salt-aleatorio"
python main_api.py
```

---

## 🐛 Troubleshooting

### Erro: "Porta 8000 já em uso"

**Windows:**

```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**

```bash
lsof -i :8000
kill -9 <PID>
```

### Erro: "Token inválido ou expirado"

Faça login novamente para obter um novo token.

### API não responde

1. Verifique se o servidor está rodando
2. Confirme que está em `http://localhost:8000`
3. Verifique logs para erros

---

## 📊 Integração com Modelo ML

A API integra automaticamente:

- Carregamento do modelo treinado
- Scoring de transações em tempo real
- Features calculadas automaticamente
- Geração de alertas quando suspeita é detectada

---

## 🚀 Próximos Passos

1. **Customize os usuários** - Edite `src/auth.py` USERS_DB
2. **Integre com seu banco de dados** - Substitua dicionário por DB real
3. **Configure alertas reais** - Altere modo `simulacao` para `real` em config.yaml
4. **Deploy em produção** - Consulte [docs/DEPLOY.md](docs/DEPLOY.md)

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte [docs/API_LOGIN.md](docs/API_LOGIN.md)
2. Verifique os logs do servidor
3. Consulte a documentação do [FastAPI](https://fastapi.tiangolo.com/)

---

**Versão:** 1.0.0  
**Última atualização:** Maio 2026
