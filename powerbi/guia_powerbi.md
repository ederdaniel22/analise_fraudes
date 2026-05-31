# Guia de Construção — Dashboard FraudShield (Power BI)

Este guia reconstrói no Power BI Desktop o mesmo projeto entregue em Python,
com **dashboards interativos** e **métricas de combate a fraude em tempo real**.

## 1. Importar os dados (star schema)
Os CSVs já tratados estão em `powerbi/dados_modelo/`:
- `fato_transacoes.csv` (200.000 linhas — tabela fato)
- `dim_tempo.csv`, `dim_canal.csv`, `dim_tipo_fraude.csv`, `dim_geografia.csv`, `dim_cliente.csv`

**Página Inicial → Obter Dados → Texto/CSV** e importe os 6 arquivos.
Marque codificação **65001 (UTF-8)**.

## 2. Modelagem (relacionamentos)
Em **Exibição de Modelo**, crie os relacionamentos (1 → *):
| Dimensão (1) | Fato (*) |
|---|---|
| dim_tempo[DataKey] | fato_transacoes[DataKey] |
| dim_canal[CanalKey] | fato_transacoes[CanalKey] |
| dim_tipo_fraude[TipoFraudeKey] | fato_transacoes[TipoFraudeKey] |
| dim_geografia[GeoKey] | fato_transacoes[GeoKey] |
| dim_cliente[Customer_ID] | fato_transacoes[Customer_ID] |

Marque `dim_tempo` como **Tabela de Datas** (campo `Data`).

## 3. Medidas
Crie as medidas do arquivo `medidas_dax.md` (Total Fraudes, Taxa de Fraude %,
Valor em Fraude, Perda Evitada, Nível de Risco, etc.).

## 4. Páginas do relatório (sugestão)

### Página 1 — Visão Executiva (diretoria)
- **Cartões (KPI):** Total Transações, Total Fraudes, Taxa de Fraude %, Valor em Fraude, Perda Evitada (Meta 85%).
- **Cartão com `Nível de Risco`** (semáforo).
- **Gráfico de barras:** Fraudes por Tipo (`dim_tipo_fraude[TipoFraude]` × `Total Fraudes`).
- **Linha:** Fraudes ao longo do tempo (`dim_tempo[Data]`).
- **Mapa:** fraudes por `dim_geografia[State]`.

### Página 2 — Monitoramento Operacional (analistas)
- Matriz: Canal × Tipo de Fraude × Taxa de Fraude %.
- Gráfico de colunas: Fraude por `Periodo_Dia` / Hora.
- Tabela detalhada de transações com `Is_Fraud = 1` (drill-through).
- Segmentações: Canal, Tipo de Conta, Faixa de Valor, Período.

### Página 3 — Tempo Real
- Conecte via **DirectQuery** ou **streaming dataset** (push API do Power BI)
  à mesma fila que alimenta o motor Python (`/score`).
- Cartões com **Tempo Médio de Alerta (s)** e **% Alertas dentro do SLA**.
- Visual de **Atualização automática da página** (Formatar página → Atualização
  automática → 5–30 s) para refletir novas transações.

## 5. Tempo real — duas opções de integração
1. **Streaming Dataset (push):** crie um dataset de streaming no Power BI Service;
   o motor Python faz `POST` dos eventos de fraude na URL de push. Visuais de bloco
   atualizam em segundos.
2. **DirectQuery** sobre um banco (PostgreSQL/SQL Server) onde o serviço Python grava
   os scores em tempo real. Combine com **atualização automática da página**.

## 6. Tema visual
Aplique o tema Neo Bank Finance: Azul `#1B3A6B`, Ciano `#2E9CCA`, Vermelho `#E4572E`,
Âmbar `#F3A712`, Verde `#2A9D8F`. (Exibição → Temas → Personalizar tema atual.)

## 7. Publicação
**Publicar → workspace Neo Bank Finance**. Configure **atualização agendada** (gateway)
e os **alertas de dados** do Power BI sobre a medida `Taxa de Fraude %`
para notificar a diretoria por e-mail quando ultrapassar o limite.
