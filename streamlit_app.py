import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

# Adiciona o diretório atual ao PATH para importar update_data
sys.path.append('.')

try:
    from update_data import coletar_links, baixar_arquivos, processar_arquivos, analisar_e_salvar
except ImportError:
    st.error("Erro: Não foi possível importar as funções de update_data.py. Certifique-se de que o arquivo existe.")
    st.stop()  # Stop the app if the import fails


@st.cache_data
def update_and_load_data():
    """
    Fetches, processes, and loads the data, caching the result.
    Returns the monthy_selecionado and df_corr dataframes.
    """
    st.write("Iniciando a atualização dos dados...")
    try:
        with st.spinner("Coletando links dos arquivos..."):
            file_links = coletar_links()
        with st.spinner("Baixando arquivos..."):
            downloaded_files = baixar_arquivos(file_links)
        with st.spinner("Processando dados dos arquivos..."):
            all_dataframes = processar_arquivos(downloaded_files)
        with st.spinner("Analisando e salvando dados..."):
            analisar_e_salvar(all_dataframes)
        st.success("Atualização dos dados concluída com sucesso!")
    except Exception as e:
        st.error(f"Ocorreu um erro durante a atualização dos dados: {e}")
        return pd.DataFrame(), pd.DataFrame() # Return empty dataframes on error

    # Load the processed data
    monthy_selecionado_df = pd.DataFrame()
    if os.path.exists('monthy_selecionado.csv'):
        try:
            monthy_selecionado_df = pd.read_csv('monthy_selecionado.csv')
            monthy_selecionado_df['Month'] = pd.to_datetime(monthy_selecionado_df['Month'], errors='coerce')
            monthy_selecionado_df.dropna(subset=['Month'], inplace=True)
            monthy_selecionado_df['Month_Str'] = monthy_selecionado_df['Month'].dt.strftime('%Y-%m')
        except Exception as e:
            st.error(f"Erro ao carregar ou processar 'monthy_selecionado.csv': {e}")
            monthy_selecionado_df = pd.DataFrame()

    # Using a placeholder for df_corr as in the previous steps
    data_corr = {
        'Month': ['2023-01', '2023-02', '2023-03', '2023-01', '2023-02', '2023-03'],
        'Node_ID': ['1006', '1006', '1006', '1007', '1007', '1007'],
        'Correlation': [0.8, 0.75, 0.9, -0.6, -0.7, -0.85]
    }
    df_corr_local = pd.DataFrame(data_corr)
    df_corr_local['Month'] = df_corr_local['Month'].astype(str)

    return monthy_selecionado_df, df_corr_local


def display_attendance_dashboard(monthy_selecionado_df):
    """Displays the monthly attendance dashboard."""
    st.header("Saude dos Dados - Porcentagem de Entrega")
    if not monthy_selecionado_df.empty and 'Node_ID' in monthy_selecionado_df.columns:
        node_id_presenca = st.selectbox(
            "Selecione um Piezômetro (Presença):",
            sorted(monthy_selecionado_df["Node_ID"].unique()),
            key="presenca_dropdown"
        )
        if node_id_presenca:
            st.subheader("Gráfico de Presença Mensal")
            try:
                df_filtrado_presenca = monthy_selecionado_df[monthy_selecionado_df["Node_ID"] == node_id_presenca].copy()
                df_filtrado_presenca = df_filtrado_presenca.sort_values(by='Month')
                fig_presenca = px.bar(
                    df_filtrado_presenca,
                    x="Month_Str",
                    y="Monthly_Attendance_Percentage",
                    title=f"Presença Mensal — Piezômetro {node_id_presenca}",
                    labels={"Month_Str": "Mês", "Monthly_Attendance_Percentage": "Porcentagem de Atendimento (%)"},
                    color="Monthly_Attendance_Percentage",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                fig_presenca.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig_presenca, use_container_width=True)
            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar o gráfico de presença: {e}")
    else:
        st.warning("Dados de presença mensal não carregados para exibição.")


def display_correlation_dashboard(df_corr_local):
    """Displays the monthly correlation dashboard."""
    st.header("Correlação Mensal (Frequência vs Pressão) por Piezômetro")
    if not df_corr_local.empty and 'Node_ID' in df_corr_local.columns:
        node_id_correlacao = st.selectbox(
            "Selecione um Piezometro (Correlação):",
            sorted(df_corr_local["Node_ID"].unique()),
            key="correlacao_dropdown"
        )
        if node_id_correlacao:
            st.subheader("Gráfico de Correlação Mensal")
            try:
                df_filtrado_corr = df_corr_local[df_corr_local["Node_ID"] == node_id_correlacao].copy()
                df_filtrado_corr['Month_sort'] = pd.to_datetime(df_filtrado_corr['Month'])
                df_filtrado_corr = df_filtrado_corr.sort_values(by='Month_sort').drop(columns=['Month_sort'])
                fig_correlacao = px.bar(
                    df_filtrado_corr,
                    x="Month",
                    y="Correlation",
                    title=f"Correlação Mensal para o Nó {node_id_correlacao}",
                    labels={"Month": "Mês", "Correlation": "Coeficiente de Correlação"},
                    color_discrete_sequence=["indianred"]
                )
                fig_correlacao.add_shape(
                    type="line", x0=-0.5, x1=len(df_filtrado_corr['Month']) - 0.5,
                    y0=-0.75, y1=-0.75, line=dict(color="Red", width=2, dash="dash")
                )
                fig_correlacao.update_layout(
                    xaxis=dict(tickmode='array', tickvals=list(range(len(df_filtrado_corr['Month']))), ticktext=df_filtrado_corr['Month']),
                    yaxis_range=[-1, 1]
                )
                st.plotly_chart(fig_correlacao, use_container_width=True)
            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar o gráfico de correlação: {e}")
    else:
        st.warning("Dados de correlação mensal não carregados para exibição.")


def main():
    """Main function to run the Streamlit application."""
    st.title("Dashboards de Análise de Dados")
    monthy_selecionado, df_corr = update_and_load_data()
    display_attendance_dashboard(monthy_selecionado)
    display_correlation_dashboard(df_corr)

if __name__ == "__main__":
    main()
