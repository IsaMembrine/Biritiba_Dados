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
                       sorted(monthy_df["Node_ID"].unique()))
        def display_attendance_dashboard(monthy_df):
    st.header("📊 Presença Mensal dos Dados")

    if monthy_df.empty:
        st.warning("Nenhum dado disponível para exibir.")
        return

    # Seleção do piezômetro
    node_id = st.selectbox("Selecione um Piezômetro:", sorted(monthy_df["Node_ID"].unique()))

    # Filtra os dados para o piezômetro escolhido
    df_filtrado = monthy_df[monthy_df["Node_ID"] == node_id]

    if df_filtrado.empty:
        st.error(f"Nenhum dado encontrado para o Node {node_id}.")
        return

    # Cria gráfico de barras interativo com Plotly
    fig = px.bar(
        df_filtrado,
        x="Month_Str",
        y="Monthly_Attendance_Percentage",
        title=f"📅 Presença Mensal – Node {node_id}",
        labels={
            "Month_Str": "Mês",
            "Monthly_Attendance_Percentage": "Presença (%)"
        },
        color="Monthly_Attendance_Percentage",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(xaxis_title="Mês", yaxis_title="% de Presença", yaxis_range=[0, 100])

    # Exibe gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Adiciona observações
    st.markdown("""
    ✅ **Legenda**: A barra representa o percentual de dados disponíveis por mês para o piezômetro selecionado.
    
    💡 Quanto mais alta a barra, maior a cobertura de dados. Ideal é estar próximo de 100%.
    """)
def display_correlation_dashboard(df_corr):
    st.header("📈 Correlação Mensal: Pressão vs Frequência")

    if df_corr.empty:
        st.warning("Nenhum dado de correlação disponível.")
        return

    # Seleciona piezômetro
    node_id = st.selectbox("Selecione um Piezômetro (Correlação):", sorted(df_corr["Node_ID"].unique()))

    # Filtra correlações para o nó escolhido
    df_filtrado = df_corr[df_corr["Node_ID"] == node_id]

    if df_filtrado.empty:
        st.error(f"Nenhum dado de correlação encontrado para o Node {node_id}.")
        return

    # Cria gráfico interativo
    fig = px.line(
        df_filtrado,
        x="Month",
        y="Correlation",
        title=f"📊 Correlação Mensal – Node {node_id}",
        labels={"Month": "Mês", "Correlation": "Correlação"},
        markers=True
    )
    fig.update_layout(
        yaxis=dict(range=[-1, 1]),
        xaxis_title="Mês",
        yaxis_title="Correlação",
        hovermode="x unified"
    )

    # Exibe o gráfico
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    ℹ️ **Interpretação**:
    - Valores próximos de `+1` indicam forte correlação positiva.
    - Valores próximos de `-1` indicam correlação negativa.
    - Valores próximos de `0` indicam pouca ou nenhuma correlação.

    🧠 Isso ajuda a avaliar o comportamento conjunto das variáveis medidas pelos sensores.
    """)
def main():
    st.title("🔎 Análise de Piezômetros")

    # Atualiza os dados e carrega os CSVs processados
    monthy_df, df_corr = update_and_load_data()

    # Cria abas para navegação
    tab1, tab2 = st.tabs(["📊 Presença Mensal", "📈 Correlação entre Variáveis"])

    with tab1:
        display_attendance_dashboard(monthy_df)

    with tab2:
        display_correlation_dashboard(df_corr)
if __name__ == "__main__":
    main()

