"""Geração dos gráficos comparativos de tipos de fraude (reports/figures)."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Paleta Neo Bank Finance
AZUL="#1B3A6B"; CIANO="#2E9CCA"; VERM="#E4572E"; AMAR="#F3A712"; VERDE="#2A9D8F"; CINZA="#6c757d"
PALETA=[AZUL,CIANO,VERM,AMAR,VERDE,CINZA]
plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
                     "axes.titleweight":"bold","figure.dpi":120})

def _salvar(fig, nome):
    p = FIG / nome
    fig.tight_layout(); fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    return p

def grafico_tipos_fraude(bank_df: pd.DataFrame):
    """Volume de fraudes detectadas por tipo (taxonomia de negócio)."""
    d = bank_df[bank_df["Is_Fraud"]==1]["Tipo_Fraude"].value_counts()
    fig, ax = plt.subplots(figsize=(9,5))
    bars = ax.barh(d.index[::-1], d.values[::-1], color=PALETA)
    ax.set_title("Fraudes Detectadas por Tipo")
    ax.set_xlabel("Nº de transações fraudulentas")
    for b in bars: ax.text(b.get_width()+max(d.values)*0.01, b.get_y()+b.get_height()/2,
                           f"{int(b.get_width()):,}".replace(",","."), va="center")
    return _salvar(fig,"01_fraudes_por_tipo.png")

def grafico_taxa_por_canal(bank_df):
    g = bank_df.groupby("Device_Type")["Is_Fraud"].mean().sort_values(ascending=False)*100
    fig,ax=plt.subplots(figsize=(8,5))
    ax.bar(g.index,g.values,color=PALETA)
    ax.set_title("Taxa de Fraude por Canal (%)"); ax.set_ylabel("% fraude")
    for i,v in enumerate(g.values): ax.text(i,v+0.03,f"{v:.2f}%",ha="center")
    return _salvar(fig,"02_taxa_por_canal.png")

def grafico_valor_distribuicao(cc_df, target):
    fig,ax=plt.subplots(figsize=(8,5))
    leg = cc_df[cc_df[target]==0]["Amount"]; fr = cc_df[cc_df[target]==1]["Amount"]
    bins=np.linspace(0, np.percentile(cc_df["Amount"],99), 40)
    ax.hist(leg,bins=bins,alpha=0.6,label="Legítima",color=CIANO,density=True)
    ax.hist(fr,bins=bins,alpha=0.7,label="Fraude",color=VERM,density=True)
    ax.set_title("Distribuição de Valor: Fraude vs Legítima")
    ax.set_xlabel("Valor da transação"); ax.set_ylabel("Densidade"); ax.legend()
    return _salvar(fig,"03_valor_fraude_vs_legitima.png")

def grafico_fraude_por_hora(bank_df):
    g = bank_df.groupby("Hora")["Is_Fraud"].mean()*100
    fig,ax=plt.subplots(figsize=(9,4.5))
    ax.plot(g.index,g.values,marker="o",color=AZUL,lw=2)
    ax.fill_between(g.index,g.values,alpha=0.15,color=AZUL)
    ax.set_title("Taxa de Fraude por Hora do Dia"); ax.set_xlabel("Hora"); ax.set_ylabel("% fraude")
    return _salvar(fig,"04_fraude_por_hora.png")

def grafico_top_estados(bank_df,k=10):
    fr = bank_df[bank_df["Is_Fraud"]==1]["State"].value_counts().head(k)
    fig,ax=plt.subplots(figsize=(9,5))
    ax.barh(fr.index[::-1],fr.values[::-1],color=AZUL)
    ax.set_title(f"Top {k} Regiões por Volume de Fraude"); ax.set_xlabel("Nº de fraudes")
    return _salvar(fig,"05_top_regioes.png")

def grafico_importancia(metrics):
    tf = metrics["top_features"][:8][::-1]
    fig,ax=plt.subplots(figsize=(8,5))
    ax.barh([t["feature"] for t in tf],[t["importancia"] for t in tf],color=VERDE)
    ax.set_title("Principais Fatores do Modelo (importância)"); ax.set_xlabel("Importância")
    return _salvar(fig,"06_importancia_modelo.png")

def grafico_matriz_confusao(metrics):
    cm=np.array(metrics["matriz_confusao"])
    fig,ax=plt.subplots(figsize=(5.5,5))
    im=ax.imshow(cm,cmap="Blues")
    ax.set_xticks([0,1]); ax.set_yticks([0,1])
    ax.set_xticklabels(["Legítima","Fraude"]); ax.set_yticklabels(["Legítima","Fraude"])
    ax.set_xlabel("Previsto"); ax.set_ylabel("Real"); ax.set_title("Matriz de Confusão")
    for i in range(2):
        for j in range(2):
            ax.text(j,i,f"{cm[i,j]:,}".replace(",","."),ha="center",
                    color="white" if cm[i,j]>cm.max()/2 else "black",fontsize=13,fontweight="bold")
    return _salvar(fig,"07_matriz_confusao.png")

def grafico_economia(bank_df, reducao=0.85):
    """Estimativa de perdas evitadas (valor fraudado * redução alvo)."""
    perda = bank_df[bank_df["Is_Fraud"]==1]["Transaction_Amount"].sum()
    fig,ax=plt.subplots(figsize=(7,5))
    vals=[perda, perda*(1-reducao)]
    ax.bar(["Sem solução","Com FraudShield"],vals,color=[VERM,VERDE])
    ax.set_title("Perdas por Fraude: Antes vs Depois (meta -85%)")
    ax.set_ylabel("Valor exposto (moeda da base)")
    for i,v in enumerate(vals): ax.text(i,v,f"{v/1e6:,.1f} M",ha="center",va="bottom")
    return _salvar(fig,"08_economia_estimada.png")
