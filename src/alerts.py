"""Disparo de alertas de fraude por E-MAIL (SMTP) e WhatsApp (Twilio).

Modo 'simulacao' registra os alertas em log (sem credenciais).
Modo 'real' envia de fato usando as credenciais do .env/config.
"""
from __future__ import annotations
import logging, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

log = logging.getLogger("fraudshield.alertas")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def montar_mensagem(tx: dict, resultado: dict) -> dict:
    nivel = "🔴 CRÍTICO" if resultado["score_fraude"] >= 0.9 else "🟠 ALTO"
    titulo = f"[FraudShield] Alerta {nivel} - Transação {tx.get('TransactionID','N/A')}"
    corpo = (
        f"Possível fraude detectada em tempo real.\n\n"
        f"Transação: {tx.get('TransactionID','N/A')}\n"
        f"Conta: {tx.get('AccountID','N/A')}\n"
        f"Valor: {tx.get('TransactionAmount','N/A')}\n"
        f"Canal: {tx.get('Channel', tx.get('Device_Type','N/A'))}\n"
        f"Local: {tx.get('Location','N/A')}\n"
        f"Score de fraude: {resultado['score_fraude']:.0%}\n"
        f"Anomalia: {'Sim' if resultado.get('anomalia') else 'Não'}\n"
        f"Tipo estimado: {resultado.get('tipo_fraude','N/A')}\n"
        f"Horário: {datetime.now():%d/%m/%Y %H:%M:%S}\n\n"
        f"Ação recomendada: bloquear transação e contatar o cliente."
    )
    cliente = (f"Olá! Detectamos uma transação suspeita de {tx.get('TransactionAmount','')} "
               f"na sua conta Neo Bank Finance. Foi você? Responda SIM ou NÃO. "
               f"Em caso de dúvida ligue 0800-NEOBANK.")
    return {"titulo": titulo, "corpo": corpo, "cliente": cliente}

# ---------------- E-MAIL ----------------
def enviar_email(cfg: dict, titulo: str, corpo: str, modo: str = "simulacao") -> bool:
    dest = cfg["email"]["destinatarios_analistas"]
    if modo != "real":
        log.info(f"[SIMULAÇÃO][EMAIL] -> {dest} | {titulo}")
        return True
    try:
        msg = MIMEMultipart(); msg["Subject"]=titulo
        msg["From"]=cfg["email"]["remetente"]; msg["To"]=", ".join(dest)
        msg.attach(MIMEText(corpo,"plain"))
        ctx=ssl.create_default_context()
        with smtplib.SMTP(cfg["email"]["smtp_host"],cfg["email"]["smtp_port"]) as s:
            s.starttls(context=ctx)
            s.login(cfg["email"]["usuario"],cfg["email"]["senha"])
            s.sendmail(cfg["email"]["remetente"],dest,msg.as_string())
        log.info(f"[REAL][EMAIL] enviado -> {dest}"); return True
    except Exception as e:
        log.error(f"Falha e-mail: {e}"); return False

# ---------------- WHATSAPP ----------------
def enviar_whatsapp(cfg: dict, texto: str, modo: str = "simulacao", para: list | None = None) -> bool:
    para = para or cfg["whatsapp"]["numeros_analistas"]
    if modo != "real":
        log.info(f"[SIMULAÇÃO][WHATSAPP] -> {para} | {texto[:80]}...")
        return True
    try:
        from twilio.rest import Client
        client=Client(cfg["whatsapp"]["twilio_account_sid"],cfg["whatsapp"]["twilio_auth_token"])
        for n in para:
            client.messages.create(body=texto, from_=cfg["whatsapp"]["numero_origem"], to=n)
        log.info(f"[REAL][WHATSAPP] enviado -> {para}"); return True
    except Exception as e:
        log.error(f"Falha WhatsApp: {e}"); return False

def disparar_alertas(cfg_alertas: dict, tx: dict, resultado: dict) -> dict:
    """Orquestra: e-mail para analistas + WhatsApp para analistas e cliente."""
    modo = cfg_alertas.get("modo","simulacao")
    m = montar_mensagem(tx, resultado)
    r_email = enviar_email(cfg_alertas, m["titulo"], m["corpo"], modo)
    r_wpp_time = enviar_whatsapp(cfg_alertas, m["corpo"], modo)
    r_wpp_cli = enviar_whatsapp(cfg_alertas, m["cliente"], modo,
                                para=[tx.get("whatsapp_cliente","whatsapp:+5511999999999")])
    return {"email_analistas": r_email, "whatsapp_analistas": r_wpp_time, "whatsapp_cliente": r_wpp_cli}
