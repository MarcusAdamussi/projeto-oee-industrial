# 🏭 Análise de OEE e Prejuízo Financeiro Industrial

## 🤖 Metodologia & Autodidatismo com IA Generativa

Para simular um ambiente corporativo real de Analytics e Engenharia de Dados, utilizei **Engenharia de Prompt** para atuar como um *Product Owner / Gerente de Operações*.

* **Criação do Cenário de Negócio:** Formulei o problema, o contexto de produção e as demandas operacionais simulando regras de negócio reais de uma planta industrial.
* **Autonomia e Resolução:** Toda a modelagem relacional do banco de dados (SQLite), a escrita das consultas SQL, a lógica dos cálculos de OEE em Python e a mensuração do impacto financeiro foram desenvolvidas e consolidadas de forma autônoma.

Esse fluxo demonstra capacidade autodidata para acelerar o aprendizado, estruturar problemas complexos e entregar soluções analíticas *end-to-end*.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Manipulação de Dados:** Pandas
* **Banco de Dados Relacional:** SQLite3
* **Linguagem de Consulta:** SQL
* **Visualização de Dados:** Matplotlib & Seaborn

---

## 📌 Problemas de Negócio & Resoluções

### 1. Visão de OEE por Turno e Máquina

> **Pergunta de Negócio:** *Qual está sendo o OEE médio da nossa fábrica nesses dias? Como ele se divide entre os pilares de Disponibilidade, Performance e Qualidade para cada máquina e turno?*

#### Lógica de Extração (SQL)
Para consolidar os tempos de parada por registro de produção, foi executado um `LEFT JOIN` com agrupamento por ordem de produção:

```sql
SELECT 
    pr.id_producao,
    pr.data_turno,
    pr.turno,
    pr.id_maquina,
    pr.qtd_planejada,
    pr.qtd_boas,
    pr.qtd_refugo,
    pr.tempo_planejado_min,
    IFNULL(SUM(p.tempo_parada_min), 0) AS tempo_parada_total
FROM tb_producao pr
LEFT JOIN tb_paradas p ON pr.id_producao = p.id_producao
GROUP BY pr.id_producao;

Processamento e Vetorização (Pandas)
Com os dados extraídos, foram calculados os três pilares do OEE e a métrica final:

# Cálculos dos Pilares do OEE
df_oee['disponibilidade'] = (df_oee['tempo_planejado_min'] - df_oee['tempo_parada_total']) / df_oee['tempo_planejado_min']
df_oee['performance'] = (df_oee['qtd_boas'] + df_oee['qtd_refugo']) / df_oee['qtd_planejada']
df_oee['qualidade'] = df_oee['qtd_boas'] / (df_oee['qtd_boas'] + df_oee['qtd_refugo'])

# OEE Final
df_oee['oee'] = df_oee['disponibilidade'] * df_oee['performance'] * df_oee['qualidade']

- Principais Insights de OEE
Pior Desempenho: A máquina INJ-01 no Turno A (02/07) registrou o menor OEE (32,50%), criticamente afetada por 220 minutos de paradas acumuladas.

Segundo Pior Caso: A máquina INJ-02 no Turno A (01/07) atingiu 34,64% de OEE, apontando o Turno A como o principal gargalo operacional da fábrica.

2. Impacto Financeiro das Paradas Não Planejadas
Pergunta de Negócio: Quanto dinheiro (R$) estamos perdendo por conta do tempo ocioso das máquinas por motivo de parada?

Agregação e Cálculo Financeiro
A consulta agrupa o tempo total parado por motivo e converte a taxa horária de custo da máquina em valores monetários reais:

SELECT 
    motivo_parada,
    SUM(tempo_parada_min) AS tempo_total_min,
    custo_hora_maquina
FROM tb_paradas
GROUP BY motivo_parada;

# Cálculo da perda financeira por conversão de horas
df_custo['prejuizo_reais'] = (df_custo['tempo_total_min'] / 60) * df_custo['custo_hora_maquina']
prejuizo_total = df_custo['prejuizo_reais'].sum()

3. Análise de Pareto (Regra 80/20) & Identificação do Gargalo
Pergunta de Negócio: Com base no gráfico de custos por motivo de parada, qual ação você recomenda para a equipe de Engenharia de Processos / Manutenção?

- Principais Insights de Pareto
Os Vilões do Orçamento: Falha Elétrica (R$ 750,00) e Falha Mecânica/Quebra (R$ 750,00) correspondem sozinhos a 61,58% de todo o prejuízo financeiro da fábrica.

Corte dos 80%: Ao somar o Setup/Troca de Molde (R$ 437,50), estes 3 motivos ultrapassam a barreira dos 80% do impacto financeiro total (atingindo ~81,38%).

- Plano de Ação Recomendado
Priorizar Manutenção Preventiva (Elétrica e Mecânica): Foco imediato nas máquinas para eliminar o maior causador de perdas financeiras (61,58%).

Implementação de SMED (Troca Rápida de Ferramenta): Otimizar o tempo do Setup de Moldes para reduzir o tempo ocioso do terceiro maior gargalo.

Despriorizar Ações Secundárias: Motivos como "Falta de Matéria-Prima" e "Ajuste de Processo" somados representam menos de 12% do prejuízo, devendo ser tratados em segundo momento.

