"""API FastAPI para FraudShield com autenticação e gestão de dados de clientes."""
from __future__ import annotations
import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Form, Header
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from .config import load_config
from .auth import (
    Token, Usuario, UsuarioLogin, UsuarioRegistro, TokenData,
    autenticar_usuario, registrar_usuario, criar_token_acesso, 
    verificar_token, obter_usuario, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .realtime_scoring import avaliar_transacao
from . import data_loader as DL
from . import features as F

log = logging.getLogger("fraudshield.api")
ROOT = Path(__file__).resolve().parents[1]

# Inicializar FastAPI
app = FastAPI(
    title="FraudShield API",
    description="Sistema de detecção de fraudes com autenticação JWT",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dados compartilhados
_cfg = None
_banco_dados = None
_clientes_cache = None

def obter_config():
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg

def obter_usuario_atual(token: str = Header(None)) -> Optional[TokenData]:
    """Dependência para obter o usuário atual do token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )
    
    token_data = verificar_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )
    return token_data

def exigir_papel(*papeis_permitidos):
    """Dependência de AUTORIZAÇÃO: garante que o usuário tem um dos papéis exigidos.
    Bloqueia, por exemplo, que um 'cliente' analise transações ou veja a base de clientes."""
    def _verifica(token_data: TokenData = Depends(obter_usuario_atual)) -> TokenData:
        if token_data.role not in papeis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Requer papel: {' ou '.join(papeis_permitidos)}."
            )
        return token_data
    return _verifica

# ==================== Endpoints de Autenticação ====================

@app.post("/api/login", response_model=Token)
def login(credenciais: UsuarioLogin):
    """Autentica um usuário e retorna um JWT token."""
    usuario = autenticar_usuario(credenciais.email, credenciais.senha)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = criar_token_acesso(
        data={"sub": usuario["email"], "role": usuario["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": usuario
    }

@app.post("/api/registrar")
def registrar(dados: UsuarioRegistro,
              token_data: TokenData = Depends(exigir_papel("analista", "admin"))):
    """Cadastra um novo cliente. Restrito a analista/admin (autocadastro público desativado)."""
    usuario = registrar_usuario(dados.email, dados.nome, dados.senha)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    return {"status": "sucesso",
            "mensagem": f"Cliente {usuario['email']} cadastrado por {token_data.email}.",
            "usuario": usuario}

@app.get("/api/perfil", response_model=Usuario)
def obter_perfil(token_data: TokenData = Depends(obter_usuario_atual)):
    """Obtém os dados do perfil do usuário autenticado."""
    usuario = obter_usuario(token_data.email)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return usuario

# ==================== Endpoints de Clientes ====================

def carregar_base_clientes():
    """Carrega a base de dados de clientes do arquivo."""
    global _clientes_cache
    
    if _clientes_cache is not None:
        return _clientes_cache
    
    try:
        cfg = obter_config()
        bank_df = DL.load_bank_transactions(cfg["dados"]["bank_transactions"])
        bank_df = F.enriquecer_bank(bank_df)
        _clientes_cache = bank_df
        return bank_df
    except Exception as e:
        log.error(f"Erro ao carregar base de clientes: {e}")
        return None

@app.get("/api/clientes")
def listar_clientes(token_data: TokenData = Depends(exigir_papel("analista", "admin")), limite: int = 100):
    """Lista clientes cadastrados."""
    df = carregar_base_clientes()
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar base de dados"
        )
    
    # Retornar apenas os primeiros registros
    resultado = df.head(limite).to_dict(orient="records")
    return {
        "total": len(df),
        "retornados": len(resultado),
        "clientes": resultado
    }

@app.get("/api/clientes/{cliente_id}")
def obter_cliente(cliente_id: str, token_data: TokenData = Depends(exigir_papel("analista", "admin"))):
    """Obtém detalhes de um cliente específico."""
    df = carregar_base_clientes()
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar base de dados"
        )
    
    # Procurar cliente por ID (ajustar coluna conforme necessário)
    cliente = df[df['AccountID'] == cliente_id].iloc[0].to_dict() if cliente_id in df['AccountID'].values else None
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente não encontrado"
        )
    
    return {"cliente": cliente}

@app.get("/api/clientes/estatisticas/resumo")
def obter_estatisticas_clientes(token_data: TokenData = Depends(exigir_papel("analista", "admin"))):
    """Obtém estatísticas gerais dos clientes."""
    df = carregar_base_clientes()
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar base de dados"
        )
    
    # Calcular estatísticas com tratamento de colunas
    fraudes = int((df['isFraud'] == 1).sum()) if 'isFraud' in df.columns else 0
    valor_total = float(df['Amount'].sum()) if 'Amount' in df.columns else 0
    valor_medio = float(df['Amount'].mean()) if 'Amount' in df.columns else 0
    
    return {
        "total_clientes": len(df),
        "total_transacoes": len(df),
        "fraudes_detectadas": fraudes,
        "valor_medio_transacao": valor_medio,
        "valor_total": valor_total
    }

# ==================== Endpoints de Análise (Scoring) ====================

@app.post("/api/analisar-transacao")
def analisar_transacao(token_data: TokenData = Depends(exigir_papel("analista", "admin")), features: dict = None, meta: dict = None):
    """Analisa uma transação individual."""
    cfg = obter_config()
    
    if not features:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Features não fornecidas"
        )
    
    try:
        resultado = avaliar_transacao({
            "features": features,
            "meta": meta or {}
        }, cfg=cfg)
        
        return {
            "status": "sucesso",
            "resultado": resultado
        }
    except Exception as e:
        log.error(f"Erro ao analisar transação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ==================== Endpoint do HTML ====================

@app.get("/", response_class=HTMLResponse)
def servir_login():
    """Retorna a página HTML de login e dashboard."""
    html_file = ROOT / "src" / "dashboard.html"
    
    if html_file.exists():
        return FileResponse(html_file)
    
    # Fallback se arquivo não existir
    return """
    <html>
    <body>
    <h1>FraudShield</h1>
    <p>Arquivo de dashboard não encontrado. Por favor, crie o arquivo dashboard.html.</p>
    </body>
    </html>
    """

@app.get("/health")
def health_check():
    """Verifica a saúde da API."""
    return {
        "status": "ok",
        "servico": "FraudShield API",
        "versao": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
