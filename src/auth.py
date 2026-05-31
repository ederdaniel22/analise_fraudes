"""Módulo de autenticação com JWT e gerenciamento de usuários."""
from __future__ import annotations
import os
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from pydantic import BaseModel

# Configuração de criptografia com hashlib (compatível com todas as plataformas)
def hash_password(senha: str) -> str:
    """Gera hash da senha usando PBKDF2."""
    salt = os.getenv("PASSWORD_SALT", "neobank-salt-dev")
    return hashlib.pbkdf2_hmac('sha256', senha.encode(), salt.encode(), 100000).hex()

def verify_password(senha_plana: str, hash_senha: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return hmac.compare_digest(hash_password(senha_plana), hash_senha)

# Chave secreta para JWT (deve ser lida de variável de ambiente em produção)
SECRET_KEY = os.getenv("SECRET_KEY", "neobank-fraudshield-secret-dev-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Banco de dados de usuários (em produção, usar um banco real)
USERS_DB = {
    "admin@neobank.com": {
        "email": "admin@neobank.com",
        "nome": "Administrador",
        "hashed_password": hash_password("admin123"),
        "role": "admin",
        "ativo": True
    },
    "analista@neobank.com": {
        "email": "analista@neobank.com",
        "nome": "Analista de Fraude",
        "hashed_password": hash_password("analista123"),
        "role": "analista",
        "ativo": True
    },
    "cliente@neobank.com": {
        "email": "cliente@neobank.com",
        "nome": "Cliente Neo Bank Finance",
        "hashed_password": hash_password("cliente123"),
        "role": "cliente",
        "ativo": True
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: dict

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class Usuario(BaseModel):
    email: str
    nome: str
    role: str
    ativo: bool

class UsuarioLogin(BaseModel):
    email: str
    senha: str

class UsuarioRegistro(BaseModel):
    email: str
    nome: str
    senha: str

def verificar_senha(senha_plana: str, hash_senha: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return verify_password(senha_plana, hash_senha)

def obter_hash_senha(senha: str) -> str:
    """Gera hash da senha."""
    return hash_password(senha)

def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Cria um JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verificar_token(token: str) -> Optional[TokenData]:
    """Verifica e decodifica um JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            return None
        return TokenData(email=email, role=role)
    except jwt.InvalidTokenError:
        return None

def autenticar_usuario(email: str, senha: str) -> Optional[dict]:
    """Autentica um usuário verificando email e senha."""
    usuario = USERS_DB.get(email)
    if not usuario or not usuario.get("ativo"):
        return None
    if not verificar_senha(senha, usuario["hashed_password"]):
        return None
    return {
        "email": usuario["email"],
        "nome": usuario["nome"],
        "role": usuario["role"]
    }

def registrar_usuario(email: str, nome: str, senha: str) -> Optional[dict]:
    """Registra um novo usuário."""
    if email in USERS_DB:
        return None  # Email já existe
    
    USERS_DB[email] = {
        "email": email,
        "nome": nome,
        "hashed_password": obter_hash_senha(senha),
        "role": "cliente",
        "ativo": True
    }
    
    return {
        "email": email,
        "nome": nome,
        "role": "cliente"
    }

def obter_usuario(email: str) -> Optional[dict]:
    """Obtém dados de um usuário."""
    usuario = USERS_DB.get(email)
    if not usuario:
        return None
    return {
        "email": usuario["email"],
        "nome": usuario["nome"],
        "role": usuario["role"],
        "ativo": usuario["ativo"]
    }
