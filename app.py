import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import os
import sys

# Adiciona o diretório atual ao PATH para importar update_data
sys.path.append('.')

try:
    from update_data import coletar_links, baixar_arquivos, processar_arquivos, analisar_e_salvar
except ImportError:
    print("Erro: Não foi possível importar as funções de update_data.py. Certifique-se de que o arquivo existe.")
    # Pode adicionar um mecanismo de fallback ou sair do aplicativo aqui

# --- Executar a atualização dos dados ---
# Esta parte será executada toda vez que o app for iniciado
print("Iniciando a atualização dos dados...")
try:
    file_links = coletar_links()
    downloaded_files = baixar_arquivos(file_links)
    all_dataframes = processar_arquivos(downloaded_files)
    analisar_e_salvar(all_dataframes) # Isso gera monthy_selecionado.csv e potencialmente dados para df_corr
    print("Atualização dos dados concluída.")
except Exception as e:
    print(f"Ocorreu um erro durante a atualização dos dados: {e}")
    # Decida como lidar com erros de atualização no seu app Dash

# --- Dashboard de Presença Mensal ---

# Verifica se o arquivo CSV existe e carrega os dados
monthy_selecionado = pd.DataFrame() # Initialize as empty DataFrame
if os.path.exists('monthy_selecionado.csv'):
    try:
        monthy_selecionado = pd.read_csv('monthy_selecionado.csv')

        # Convert Month to datetime objects explicitly if necessary
        if isinstance(monthy_selecionado["Month"].dtype, pd.PeriodDtype):
            monthy_selecionado.loc[:, "Month"] = monthy_selecionado["Month"].dt.to_timestamp()

        # Ensure 'Month' is in datetime format and then format as string 'YYYY-MM'
        monthy_selecionado.loc[:, "Month"] = pd.to_datetime(monthy_selecionado["Month"], errors='coerce')
        monthy_selecionado.dropna(subset=["Month"], inplace=True)
        monthy_selecionado.loc[:, "Month_Str"] = monthy_selecionado["Month"].dt.strftime('%Y-%m')

    except Exception as e:
        print(f"Erro ao carregar ou processar 'monthy_selecionado.csv': {e}")


# --- Dashboard de Correlação Mensal ---

# Assume df_corr contains the monthly correlation data
# ** Você precisará gerar df_corr com os dados de correlação dentro de analisar_e_salvar
# ou carregar/gerar aqui APÓS a execução da atualização **
# Exemplo (remova ou modifique conforme necessário):
data_corr = {
    'Month': ['2023-01', '2023-02', '2023-03', '2023-01', '2023-02', '2023-03'],
    'Node_ID': ['1006', '1006', '1006', '1007', '1007', '1007'],
    'Correlation': [0.8, 0.75, 0.9, -0.6, -0.7, -0.85]
}
df_corr = pd.DataFrame(data_corr) # Placeholder df_corr

# Make sure the 'Month' column is treated as a string for consistent plotting
df_corr['Month'] = df_corr['Month'].astype(str)

# Initialize the Dash app
# Para ter múltiplos layouts ou páginas, a estrutura seria diferente.
# Aqui, vamos apenas inicializar UMA instância do app e adicionar os layouts.
app = Dash(__name__)

# Combinando layouts (exemplo simples - pode ser mais complexo para múltiplos dashboards)
app.layout = html.Div([
    html.H1("Dashboards de Análise de Dados", style={'textAlign': 'center'}),

    # Layout do dashboard de Presença Mensal
    html.Div([
        html.H1("Saude dos Dados - Porcentagem de Entrega", style={'textAlign': 'center'}),

        html.Label("Selecione um Piezômetro:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id="node_dropdown",
            options=[{"label": node, "value": node} for node in sorted(monthy_selecionado["Node_ID"].unique())] if not monthy_selecionado.empty else [],
            value=monthy_selecionado["Node_ID"].unique()[0] if not monthy_selecionado.empty else None,
            clearable=False
        ),

        dcc.Graph(id="grafico_presenca")
    ], style={'border': '1px solid #ccc', 'padding': '20px', 'margin-bottom': '20px'}), # Add some styling

    html.Hr(), # Add a horizontal rule as a separator

    # Layout do dashboard de Correlação Mensal
    html.Div([
        html.H1("Correlação Mensal (Frequência vs Pressão) por Piezômetro", style={'textAlign': 'center'}),

        html.Label("Selecione um Piezometro:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id="node_dropdown_corr",
            options=[{"label": node, "value": node} for node in sorted(df_corr["Node_ID"].unique())] if not df_corr.empty else [],
            value=df_corr["Node_ID"].unique()[0] if not df_corr.empty else None,
            clearable=False
        ),

        dcc.Graph(id="grafico_correlacao_mensal")
    ], style={'border': '1px solid #ccc', 'padding': '20px'}) # Add some styling
])


# 🎯 Callback para atualizar o gráfico de Presença
@app.callback(
    Output("grafico_presenca", "figure"),
    Input("node_dropdown", "value")
)
def update_graph_presenca(node_id):
    if node_id is None or monthy_selecionado.empty:
        return {} # Return empty figure if no node is selected or data is empty

    df_filtrado = monthy_selecionado[monthy_selecionado["Node_ID"] == node_id].copy() # Use .copy() to avoid SettingWithCopyWarning

    # Ensure 'Month_Str' is sorted to maintain chronological order on the axis
    df_filtrado = df_filtrado.sort_values(by='Month')


    fig = px.bar(
        df_filtrado,
        x="Month_Str", # Use the string formatted month
        y="Monthly_Attendance_Percentage",
        title=f"Presença Mensal — {node_id}",
        labels={"Month_Str": "Mês", "Monthly_Attendance_Percentage": "Porcentagem de Atendimento (%)"},
        color="Monthly_Attendance_Percentage", # Color the bars by percentage
        color_continuous_scale=px.colors.sequential.Viridis # Choose a color scale
    )

    fig.update_layout(yaxis_range=[0, 100]) # Ensure y-axis goes from 0 to 100

    return fig


# 🎯 Callback para atualizar o gráfico de Correlação
@app.callback(
    Output("grafico_correlacao_mensal", "figure"),
    Input("node_dropdown_corr", "value")
)
def update_correlation_graph(node_id):
    if node_id is None or df_corr.empty:
        return {} # Return empty figure if no node is selected or data is empty

    df_filtrado_corr = df_corr[df_corr["Node_ID"] == node_id].copy()

    # Ensure the months are sorted for chronological order on the axis
    # Convert 'Month' back to datetime for sorting, then format to string for plotting if needed
    df_filtrado_corr['Month_sort'] = pd.to_datetime(df_filtrado_corr['Month'])
    df_filtrado_corr = df_filtrado_corr.sort_values(by='Month_sort')
    df_filtrado_corr = df_filtrado_corr.drop(columns=['Month_sort'])


    fig = px.bar(
        df_filtrado_corr,
        x="Month",
        y="Correlation",
        title=f"Correlação Mensal para o Nó {node_id}",
        labels={"Month": "Mês", "Correlation": "Coeficiente de Correlação"},
        color_discrete_sequence=["indianred"]
    )

    # Add horizontal line at y = -0.75, extending to the edges of the plot
    fig.add_shape(
        type="line",
        x0=-0.5, # Start just before the first bar
        x1=len(df_filtrado_corr['Month']) - 0.5, # End just after the last bar
        y0=-0.75,
        y1=-0.75,
        line=dict(
            color="Red",
            width=2,
            dash="dash",
        )
    )

    fig.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = list(range(len(df_filtrado_corr['Month']))),
            ticktext = df_filtrado_corr['Month']
        ),
        yaxis_range=[-1, 1] # Ensure y-axis goes from -1 to 1 for correlation
    )


    return fig


# 🏃‍♀️ Executa o app (apenas para execução local/direta)
# Para implantar, você geralmente não usaria app.run_server() diretamente aqui.
# if __name__ == '__main__':
#     app.run_server(debug=True)
