import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Força o Pandas a mostrar todas as colunas e linhas no terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# 1. Cria/Conecta ao banco SQLite local
conn = sqlite3.connect("industria_piloto.db")
cursor = conn.cursor()

# 2. Criação das tabelas
cursor.executescript("""
DROP TABLE IF EXISTS tb_paradas;
DROP TABLE IF EXISTS tb_producao;

CREATE TABLE tb_producao (
    id_producao INTEGER PRIMARY KEY AUTOINCREMENT,
    data_turno TEXT NOT NULL,
    turno TEXT NOT NULL,
    id_maquina TEXT NOT NULL,
    qtd_planejada INTEGER NOT NULL,
    qtd_boas INTEGER NOT NULL,
    qtd_refugo INTEGER NOT NULL,
    tempo_planejado_min INTEGER NOT NULL
);

CREATE TABLE tb_paradas (
    id_parada INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producao INTEGER,
    motivo_parada TEXT NOT NULL,
    tempo_parada_min INTEGER NOT NULL,
    custo_hora_maquina REAL NOT NULL,
    FOREIGN KEY (id_producao) REFERENCES tb_producao(id_producao)
);
""")

# 3. Inserção dos dados brutos do chão de fábrica
cursor.executescript("""
INSERT INTO tb_producao (data_turno, turno, id_maquina, qtd_planejada, qtd_boas, qtd_refugo, tempo_planejado_min) VALUES
('2026-07-01', 'Turno A', 'INJ-01', 1000, 850, 50, 480),
('2026-07-01', 'Turno B', 'INJ-01', 1000, 910, 20, 480),
('2026-07-01', 'Turno A', 'INJ-02', 1200, 700, 100, 480),
('2026-07-02', 'Turno A', 'INJ-01', 1000, 600, 80, 480),
('2026-07-02', 'Turno B', 'INJ-02', 1200, 1100, 15, 480);

INSERT INTO tb_paradas (id_producao, motivo_parada, tempo_parada_min, custo_hora_maquina) VALUES
(1, 'Setup/Troca de Molde', 60, 250.00),
(1, 'Falta de Matéria-Prima', 30, 250.00),
(2, 'Ajuste de Processo', 20, 250.00),
(3, 'Falha Mecânica (Quebra)', 150, 300.00),
(3, 'Setup/Troca de Molde', 45, 300.00),
(4, 'Falha Elétrica', 180, 250.00),
(4, 'Manutenção Preventiva', 40, 250.00),
(5, 'Ajuste de Processo', 15, 300.00);
""")

conn.commit()
print("Banco de dados 'industria_piloto.db' criado e populado com sucesso!\n")

# ==============================================================================
# PERGUNTA 1: CÁLCULO DO OEE
# ==============================================================================

query_sql = """
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
"""

df_oee = pd.read_sql_query(query_sql, conn)

# Cálculos dos Pilares do OEE
df_oee['disponibilidade'] = (df_oee['tempo_planejado_min'] - df_oee['tempo_parada_total']) / df_oee['tempo_planejado_min']
df_oee['performance'] = (df_oee['qtd_boas'] + df_oee['qtd_refugo']) / df_oee['qtd_planejada']
df_oee['qualidade'] = df_oee['qtd_boas'] / (df_oee['qtd_boas'] + df_oee['qtd_refugo'])

# OEE Final
df_oee['oee'] = df_oee['disponibilidade'] * df_oee['performance'] * df_oee['qualidade']
df_oee[['disponibilidade', 'performance', 'qualidade', 'oee']] = df_oee[['disponibilidade', 'performance', 'qualidade', 'oee']].round(4)

colunas_analise = ['data_turno', 'turno', 'id_maquina', 'disponibilidade', 'performance', 'qualidade', 'oee']
print("--- RESUMO EXECUTIVO DE OEE POR TURNO ---")
print(df_oee[colunas_analise])

# ==============================================================================
# PERGUNTA 2: IMPACTO FINANCEIRO DAS PARADAS
# ==============================================================================

query_custo_sql = """
    SELECT 
        motivo_parada,
        SUM(tempo_parada_min) AS tempo_total_min,
        custo_hora_maquina
    FROM tb_paradas
    GROUP BY motivo_parada;
"""

df_custo = pd.read_sql_query(query_custo_sql, conn)
df_custo['prejuizo_reais'] = ((df_custo['tempo_total_min'] / 60) * df_custo['custo_hora_maquina']).round(2)

prejuizo_total = df_custo['prejuizo_reais'].sum()
df_custo['porcentagem'] = ((df_custo['prejuizo_reais'] / prejuizo_total) * 100).round(2)
df_custo = df_custo.sort_values(by='prejuizo_reais', ascending=False).reset_index(drop=True)

print("\n--- PREJUÍZO FINANCEIRO POR MOTIVO DE PARADA ---")
print(df_custo[['motivo_parada', 'tempo_total_min', 'prejuizo_reais', 'porcentagem']])
print(f"\n💰 PREJUÍZO TOTAL DAS PARADAS: R$ {prejuizo_total:,.2f}\n")

conn.close()

# ==============================================================================
# PERGUNTA 3: O MAIOR GARGALO (PARETO)
# ==============================================================================

# Calcula a Porcentagem Acumulada usando os dados vindos direto do SQL
df_custo['pct_acumulado'] = (df_custo['prejuizo_reais'].cumsum() / prejuizo_total) * 100

# Configuração visual do gráfico
fig, ax1 = plt.subplots(figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Eixo Y1: Barras do Prejuízo Financeiro (R$)
bars = ax1.bar(df_custo['motivo_parada'], df_custo['prejuizo_reais'], color='#2b5c8f', width=0.5, label='Prejuízo (R$)')
ax1.set_ylabel('Prejuízo Financeiro (R$)', color='#2b5c8f', fontweight='bold', fontsize=12)
ax1.set_title('Gráfico de Pareto: Impacto Financeiro dos Motivos de Parada', fontsize=14, fontweight='bold', pad=15)
ax1.tick_params(axis='y', labelcolor='#2b5c8f')
ax1.set_ylim(0, df_custo['prejuizo_reais'].max() * 1.2)

# Rótulos nas barras
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f'R$ {height:,.2f}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 3),  
                 textcoords="offset points",
                 ha='center', va='bottom', fontsize=9, fontweight='bold')

# Eixo Y2: Linha da Porcentagem Acumulada (%)
ax2 = ax1.twinx()
ax2.plot(df_custo['motivo_parada'], df_custo['pct_acumulado'], color='#d9534f', marker='o', linewidth=2.5, label='% Acumulado')
ax2.set_ylabel('Porcentagem Acumulada (%)', color='#d9534f', fontweight='bold', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#d9534f')
ax2.set_ylim(0, 105)

# Linha limite de 80% (Regra de Pareto)
ax2.axhline(80, color='gray', linestyle='--', alpha=0.7)
ax2.text(len(df_custo)-1, 81, 'Corte 80%', color='gray', ha='right', fontsize=10, fontstyle='italic')

# Ajuste nos rótulos do eixo X
ax1.set_xticklabels(df_custo['motivo_parada'], rotation=20, ha='right', fontsize=10)

plt.tight_layout()
plt.savefig('pareto_paradas.png', bbox_inches='tight') # Salva a imagem para usar no README
plt.show()