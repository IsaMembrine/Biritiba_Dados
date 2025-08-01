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
    st.error("Erro: Não foi possível importar funções de update_data.py.")
    st.stop()

@st.cache_data
def update_and_load_data():
    st.write("Iniciando a atualização dos dados...")
    try:
        with st.spinner("Coletando links..."):
            file_links = coletar_links()
        with st.spinner("Baixando arquivos..."):
            downloaded_files = baixar_arquivos(file_links)
        with st.spinner("Processando dados..."):
            all_dataframes = processar_arquivos(downloaded_files)
        with st.spinner("Analisando e salvando..."):
            analisar_e_salvar(all_dataframes)
        st.success("Atualização concluída!")
    except Exception as e:
        st.error(f"Erro durante atualização: {e}")
        return pd.DataFrame(), pd.DataFrame()

    monthy_selecionado_df = pd.read_csv('monthy_selecionado.csv')
    monthy_selecionado_df['Month'] = pd.to_datetime(monthy_selecionado_df['Month'], errors='coerce')
    monthy_selecionado_df.dropna(subset=['Month'], inplace=True)
    monthy_selecionado_df['Month_Str'] = monthy_selecionado_df['Month'].dt.strftime('%Y-%m')

    df_corr_local = pd.read_csv('correlacoes_mensais.csv')
    df_corr_local['Month'] = pd.to_datetime(df_corr_local['Month'], format='%Y-%m').dt.strftime('%Y-%m')

    return monthy_selecionado_df, df_corr_local

def display_attendance_dashboard(monthy_df):
    st.header("Saúde dos Dados - Presença Mensal")
    if not monthy_df.empty and 'Node_ID' in monthy_df.columns:
        node_id = st.selectbox("Selecione um Piezômetro (Presença):",
                               sorted(monthy_df["Node_ID"].unique()))
        if node_id:
            st.subheader(f"Presença Mensal — Piezômetro {node_id}")
            df_filtrado = monthy_df[monthy_df["Node_ID"] == node_id].sort_values(by='Month')
            fig = px.bar(
                df_filtrado,
                x="Month_Str",
                y="Monthly_Attendance_Percentage",
                labels={"Month_Str": "Mês", "Monthly_Attendance_Percentage": "Presença (%)"},
                color="Monthly_Attendance_Percentage",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados de presença não disponíveis.")

def display_correlation_dashboard(df_corr):
    st.header("Correlação Mensal (Frequência vs Pressão)")
    if not df_corr.empty and 'Node_ID' in df_corr.columns:
        node_id = st.selectbox("Selecione um Piezômetro (Correlação):",
                               sorted(df_corr["Node_ID"].unique()))
        if node_id:
            st.subheader(f"Correlação Mensal — Piezômetro {node_id}")
            df_filtrado = df_corr[df_corr["Node_ID"] == node_id].copy()
            df_filtrado['Month_sort'] = pd.to_datetime(df_filtrado['Month'])
            df_filtrado = df_filtrado.sort_values(by='Month_sort').drop(columns=['Month_sort'])
            fig = px.bar(
                df_filtrado,
                x="Month",
                y="Correlation",
                labels={"Month": "Mês", "Correlation": "Correlação"},
                color_discrete_sequence=["indianred"]
            )
            fig.add_shape(
                type="line",
                x0=-0.5, x1=len(df_filtrado['Month']) - 0.5,
                y0=-0.75, y1=-0.75,
                line=dict(color="Red", width=2, dash="dash")
            )
            fig.update_layout(yaxis_range=[-1, 1])
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados de correlação não disponíveis.")

def main():
    st.title("📊 Dashboards de Análise dos Piezômetros")
    monthy_df, df_corr = update_and_load_data()
    display_attendance_dashboard(monthy_df)
    display_correlation_dashboard(df_corr)

if __name__ == "__main__":
    main()
