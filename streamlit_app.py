import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# Adiciona diretório atual ao path
sys.path.append('.')
try:
    from update_data import coletar_links, baixar_arquivos, processar_arquivos, analisar_e_salvar
except ImportError:
    st.error("Erro ao importar funções de update_data.py.")
    st.stop()

@st.cache_data
def update_and_load_data():
    st.write("🔄 Atualizando dados...")
    try:
        file_links = coletar_links()
        downloaded_files = baixar_arquivos(file_links)
        all_dataframes = processar_arquivos(downloaded_files)
        analisar_e_salvar(all_dataframes)

        if not os.path.exists('monthy_selecionado.csv') or not os.path.exists('correlacoes_mensais.csv'):
            st.error("❌ Arquivos CSV não encontrados. Verifique se o processamento foi concluído.")
            return pd.DataFrame(), pd.DataFrame()

    except Exception as e:
        st.error(f"💥 Erro na atualização dos dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        monthy_selecionado_df = pd.read_csv('monthy_selecionado.csv')
        monthy_selecionado_df['Month'] = pd.to_datetime(monthy_selecionado_df['Month'], errors='coerce')
        monthy_selecionado_df.dropna(subset=['Month'], inplace=True)
        monthy_selecionado_df['Month_Str'] = monthy_selecionado_df['Month'].dt.strftime('%Y-%m')

        df_corr_local = pd.read_csv('correlacoes_mensais.csv')
        df_corr_local['Month'] = pd.to_datetime(df_corr_local['Month'], format='%Y-%m').dt.strftime('%Y-%m')

    except Exception as e:
        st.error(f"⚠️ Erro ao carregar CSVs: {e}")
        return pd.DataFrame(), pd.DataFrame()

    return monthy_selecionado_df, df_corr_local

def display_attendance_dashboard(monthy_df):
    st.header("📊 Presença Mensal dos Dados")
    if not monthy_df.empty:
        node_id = st.selectbox("Selecione um Piezômetro (Presença):",
                               sorted(monthy_df["Node_ID"].
