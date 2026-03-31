import streamlit as st
import smartsheet
import pandas as pd
import re

# --- 1. CONFIGURAÇÕES E CUSTOS ATUALIZADOS ---
TOKEN = '32M5yHYGUMBRyOTkf3GstuBbJ36Q4T9TvefrX'
SHEET_ID = 3432321207193476 

custo_setor_map = {
    "Almoxarifado": 0.0, "Apoio a Produção": 0.0, "Calandra": 30.08,
    "Comercial": 0.0, "Descarregamento": 0.0, "Escareação": 40.04,
    "Engenharia de Produto": 0.0, "Frisadeira": 57.03, "Furadeira de bancada": 21.34,
    "Furadeira máquina": 21.34, "Guilhotina": 0.0, "Jato": 76.40,
    "Laser": 120.0, "Lixadeira (anel)": 40.04, "Lixadeira (solda)": 40.04,
    "Logística": 0.0, "Manutenção": 0.0, "Metrologia": 0.0,
    "Matéria-prima": 0.0, "Pintura": 27.14, "Plasma": 0.0,
    "Prensa": 30.8, "PPCP": 0.0, "Ponteação": 21.34,
    "Recebimento": 0.0, "Retifica": 40.04, "Sistema de Gestão da Qualidade": 0.0,
    "Solda Roda": 59.15, "Solda Tartaruga": 59.15, "Suspensão": 27.14,
    "Teste de LP": 11.91, "Torno Convencional": 13.69, "Usinagem": 50.23,
    "Rebarba": 40.04
}

@st.cache_data(ttl=300)
def buscar_tempos_unicos():
    try:
        smart = smartsheet.Smartsheet(TOKEN)
        sheet = smart.Sheets.get_sheet(SHEET_ID)
        columns = [col.title for col in sheet.columns]
        rows = [[cell.value for cell in row.cells] for row in sheet.rows]
        df = pd.DataFrame(rows, columns=columns)
        
        # Filtra apenas Retrabalho
        df = df[df['Tratativa'].astype(str).str.contains('Retrabalho', case=False, na=False)].copy()
        
        # Limpa o tempo (ex: "40 min" -> 40)
        def limpar_tempo(v):
            if v is None: return 0
            num = re.findall(r'\d+', str(v))
            return int(num[0]) if num else 0

        df['Tempo_Min'] = df['Tempo de retrabalho'].apply(limpar_tempo)
        
        # Retorna apenas Setor e Tempo (Removendo duplicados)
        return df[['Setor que retrabalhou', 'Tempo_Min']].drop_duplicates()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- 2. INTERFACE ---
st.set_page_config(page_title="Tabela de Preços de Retrabalho", layout="centered")
st.title("Tabela de Tempos e Custos")

df_base = buscar_tempos_unicos()

# Seleção do Setor
setor_sel = st.selectbox("Selecione o Setor:", sorted(list(custo_setor_map.keys())))
custo_h = custo_setor_map[setor_sel]

# Filtra tempos únicos do setor
df_exibir = df_base[df_base['Setor que retrabalhou'] == setor_sel].copy()

if not df_exibir.empty:
    # Cálculo do Custo
    df_exibir['Custo'] = (df_exibir['Tempo_Min'] * custo_h) / 60
    
    # Formatação Final
    df_exibir = df_exibir.rename(columns={'Tempo_Min': 'Tempo (min)'})
    df_exibir['Custo'] = df_exibir['Custo'].apply(lambda x: f"R$ {x:.2f}")
    
    # Exibe apenas Tempo e Custo
    st.table(df_exibir[['Tempo (min)', 'Custo']].sort_values(by='Tempo (min)'))
else:
    st.info(f"Nenhum tempo histórico registrado para o setor {setor_sel} no Smartsheet.")

# --- 3. CALCULADORA RÁPIDA ---
st.divider()
st.subheader("Calculadora Manual")
c1, c2 = st.columns(2)
with c1:
    t_manual = st.number_input("Digite o tempo (min):", min_value=0, step=1)
with c2:
    total_c = (t_manual * custo_h) / 60
    st.metric(f"Custo para {setor_sel}", f"R$ {total_c:.2f}")