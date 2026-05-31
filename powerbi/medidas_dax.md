# Medidas DAX — FraudShield (Power BI)

Cole estas medidas na tabela `fato_transacoes` (ou numa tabela vazia `_Medidas`).
O modelo segue um **star schema**: `fato_transacoes` no centro, ligada a
`dim_tempo (DataKey)`, `dim_canal (CanalKey)`, `dim_tipo_fraude (TipoFraudeKey)`,
`dim_geografia (GeoKey)` e `dim_cliente (Customer_ID)`.

## 1. Volumes e KPIs principais

```DAX
Total Transações = COUNTROWS ( fato_transacoes )

Total Fraudes = CALCULATE ( [Total Transações], fato_transacoes[Is_Fraud] = 1 )

Taxa de Fraude % =
DIVIDE ( [Total Fraudes], [Total Transações], 0 )

Valor Total Transacionado = SUM ( fato_transacoes[Valor] )

Valor em Fraude =
CALCULATE ( SUM ( fato_transacoes[Valor] ), fato_transacoes[Is_Fraud] = 1 )

Ticket Médio Fraude =
DIVIDE ( [Valor em Fraude], [Total Fraudes], 0 )
```

## 2. Métricas de combate / eficiência (tempo real)

```DAX
-- Meta de redução de 85% (PPT da diretoria)
Perda Evitada (Meta 85%) = [Valor em Fraude] * 0.85

Perda Residual Estimada = [Valor em Fraude] * 0.15

-- SLA de alerta (< 30s). Requer coluna fato_transacoes[Segundos_Ate_Alerta]
Tempo Médio de Alerta (s) = AVERAGE ( fato_transacoes[Segundos_Ate_Alerta] )

% Alertas dentro do SLA =
VAR _dentro = CALCULATE ( [Total Transações], fato_transacoes[Segundos_Ate_Alerta] <= 30 )
RETURN DIVIDE ( _dentro, [Total Fraudes], 0 )
```

## 3. Comparação por tipo de fraude

```DAX
Fraudes por Tipo =
CALCULATE ( [Total Fraudes], ALLEXCEPT ( dim_tipo_fraude, dim_tipo_fraude[TipoFraude] ) )

% do Total de Fraudes =
DIVIDE ( [Total Fraudes], CALCULATE ( [Total Fraudes], ALL ( dim_tipo_fraude ) ), 0 )

Ranking Tipo de Fraude =
RANKX ( ALL ( dim_tipo_fraude[TipoFraude] ), [Total Fraudes],, DESC )
```

## 4. Inteligência de tempo (tendência)

```DAX
Fraudes Mês Anterior =
CALCULATE ( [Total Fraudes], DATEADD ( dim_tempo[Data], -1, MONTH ) )

Variação Fraude MoM % =
DIVIDE ( [Total Fraudes] - [Fraudes Mês Anterior], [Fraudes Mês Anterior], 0 )

Fraudes Acumuladas (YTD) =
TOTALYTD ( [Total Fraudes], dim_tempo[Data] )
```

## 5. Alerta visual (semáforo de risco)

```DAX
Nível de Risco =
SWITCH ( TRUE (),
    [Taxa de Fraude %] >= 0.08, "🔴 Crítico",
    [Taxa de Fraude %] >= 0.05, "🟠 Alto",
    [Taxa de Fraude %] >= 0.03, "🟡 Moderado",
    "🟢 Controlado"
)
```

## 6. Coluna calculada — período do dia (em dim_tempo ou fato)

```DAX
Periodo_Dia =
SWITCH ( TRUE (),
    fato_transacoes[Hora] < 6,  "Madrugada",
    fato_transacoes[Hora] < 12, "Manhã",
    fato_transacoes[Hora] < 18, "Tarde",
    "Noite"
)
```
