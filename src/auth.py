"""Autenticação com JWT e gerenciamento de usuários.

Backend de banco com compatibilidade dupla:
  - Se DATABASE_URL estiver definida (ex.: PostgreSQL no Render), usa PostgreSQL (psycopg).
  - Caso contrário, usa SQLite local em data/fraudshield.db.

Senhas: PBKDF2-HMAC-SHA256 com salt individual por usuário.
Hierarquia de cadastro: admin cria analistas; analistas criam clientes.
"""
from __future__ import annotations
import os
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
import jwt
from pydantic import BaseModel

log = logging.getLogger("fraudshield.auth")
ROOT = Path(__file__).resolve().parents[1]

SECRET_KEY = os.getenv("SECRET_KEY", "neobank-fraudshield-secret-dev-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
PBKDF2_ITERACOES = 200000
PAPEIS_VALIDOS = ("admin", "analista", "cliente")
DB_PATH = Path(os.getenv("FRAUDSHIELD_DB", str(ROOT / "data" / "fraudshield.db")))

# ----------------------------------------------------------------------------
# Seleção do backend (PostgreSQL via DATABASE_URL ou SQLite local)
# ----------------------------------------------------------------------------
_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_PG = False
if _DATABASE_URL:
    try:
        import psycopg
        from psycopg.rows import dict_row
        # alguns provedores entregam 'postgres://'; psycopg quer 'postgresql://'
        if _DATABASE_URL.startswith("postgres://"):
            _DATABASE_URL = "postgresql://" + _DATABASE_URL[len("postgres://"):]
        USE_PG = True
        log.info("auth: usando PostgreSQL (DATABASE_URL)")
    except Exception as e:  # psycopg ausente -> cai para SQLite
        log.warning(f"auth: DATABASE_URL definida mas psycopg indisponível ({e}); usando SQLite")

if not USE_PG:
    import sqlite3

# Placeholder e tipo de chave conforme o backend
PH = "%s" if USE_PG else "?"
_PK = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"


def _connect():
    if USE_PG:
        return psycopg.connect(_DATABASE_URL, row_factory=dict_row)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    return con


# ----------------------------------------------------------------------------
# Hash de senha com salt individual
# ----------------------------------------------------------------------------
def _hash_com_salt(senha: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), PBKDF2_ITERACOES).hex()

def gerar_hash_senha(senha: str):
    """Retorna (salt, hash) com um salt novo e aleatorio para cada usuario."""
    salt = secrets.token_hex(16)
    return salt, _hash_com_salt(senha, salt)

def verificar_senha(senha_plana: str, salt: str, hash_senha: str) -> bool:
    return hmac.compare_digest(_hash_com_salt(senha_plana, salt), hash_senha)


# ----------------------------------------------------------------------------
# Banco de dados
# ----------------------------------------------------------------------------
def init_db():
    """Cria a tabela (se nao existir) e semeia o admin inicial."""
    ddl = (
        "CREATE TABLE IF NOT EXISTS usuarios ("
        f" id {_PK},"
        " email TEXT UNIQUE NOT NULL,"
        " nome TEXT NOT NULL,"
        " salt TEXT NOT NULL,"
        " senha_hash TEXT NOT NULL,"
        " role TEXT NOT NULL DEFAULT 'cliente',"
        " ativo INTEGER NOT NULL DEFAULT 1,"
        " criado_por TEXT,"
        " criado_em TEXT NOT NULL)"
    )
    with _connect() as con:
        con.execute(ddl)
        con.commit()
    _semear_usuarios_iniciais()

def _semear_usuarios_iniciais():
    """Cria o admin (sempre) e, se SEED_DEMO ativo, analista e cliente de demonstracao."""
    admin_email = os.getenv("ADMIN_EMAIL", "admin@neobank.com")
    if obter_usuario(admin_email) is None:
        _inserir_usuario(admin_email, "Administrador",
                         os.getenv("ADMIN_PASSWORD", "admin123"), "admin", "sistema")
    if os.getenv("SEED_DEMO", "1").lower() in ("1", "true", "sim", "yes"):
        if obter_usuario("analista@neobank.com") is None:
            _inserir_usuario("analista@neobank.com", "Analista de Fraude",
                             os.getenv("ANALISTA_PASSWORD", "analista123"), "analista", "sistema")
        if obter_usuario("cliente@neobank.com") is None:
            _inserir_usuario("cliente@neobank.com", "Cliente Neo Bank Finance",
                             os.getenv("CLIENTE_PASSWORD", "cliente123"), "cliente", "sistema")

def _inserir_usuario(email: str, nome: str, senha: str, role: str, criado_por):
    salt, h = gerar_hash_senha(senha)
    sql = (
        "INSERT INTO usuarios (email, nome, salt, senha_hash, role, ativo, criado_por, criado_em)"
        f" VALUES ({PH},{PH},{PH},{PH},{PH},1,{PH},{PH})"
    )
    with _connect() as con:
        con.execute(sql, (email.lower().strip(), nome, salt, h, role, criado_por,
                          datetime.now(timezone.utc).isoformat()))
        con.commit()


# ----------------------------------------------------------------------------
# Modelos (Pydantic)
# ----------------------------------------------------------------------------
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
    role: Optional[str] = "cliente"


# ----------------------------------------------------------------------------
# Tokens JWT
# ----------------------------------------------------------------------------
def criar_token_acesso(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            return None
        return TokenData(email=email, role=payload.get("role"))
    except jwt.InvalidTokenError:
        return None


# ----------------------------------------------------------------------------
# Operacoes de usuario
# ----------------------------------------------------------------------------
def obter_usuario(email: str):
    with _connect() as con:
        row = con.execute(f"SELECT email, nome, role, ativo FROM usuarios WHERE email = {PH}",
                          (email.lower().strip(),)).fetchone()
    if not row:
        return None
    return {"email": row["email"], "nome": row["nome"], "role": row["role"], "ativo": bool(row["ativo"])}

def autenticar_usuario(email: str, senha: str):
    with _connect() as con:
        row = con.execute(f"SELECT * FROM usuarios WHERE email = {PH}", (email.lower().strip(),)).fetchone()
    if not row or not row["ativo"]:
        return None
    if not verificar_senha(senha, row["salt"], row["senha_hash"]):
        return None
    return {"email": row["email"], "nome": row["nome"], "role": row["role"]}

def registrar_usuario(email: str, nome: str, senha: str, role: str = "cliente", criado_por=None):
    """Cria um usuario. Retorna None se o e-mail ja existir ou o papel for invalido."""
    role = (role or "cliente").lower()
    if role not in PAPEIS_VALIDOS:
        return None
    if obter_usuario(email) is not None:
        return None
    _inserir_usuario(email, nome, senha, role, criado_por)
    return {"email": email.lower().strip(), "nome": nome, "role": role}

def listar_usuarios():
    with _connect() as con:
        rows = con.execute(
            "SELECT email, nome, role, ativo, criado_por, criado_em FROM usuarios ORDER BY criado_em").fetchall()
    return [{"email": r["email"], "nome": r["nome"], "role": r["role"], "ativo": bool(r["ativo"]),
             "criado_por": r["criado_por"], "criado_em": r["criado_em"]} for r in rows]


# Inicializa o banco ao importar o modulo (idempotente).
init_db()
