import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import process_omie_data

st.set_page_config(layout="wide")

st.title("Dashboard de Conciliação OMIE")

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Escolha um arquivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("Arquivo carregado com sucesso!")

        # Processar os dados usando a função do outro arquivo
        df_processado = process_omie_data.process_data(df)

        st.subheader("Dados Processados")
        st.dataframe(df_processado)

        # Análise e Visualização
        st.subheader("Análise de Contas a Pagar e Receber")

        # Converter colunas de data para datetime
        df_processado['Data de Vencimento'] = pd.to_datetime(df_processado['Data de Vencimento'], errors='coerce')
        df_processado['Data de Previsão'] = pd.to_datetime(df_processado['Data de Previsão'], errors='coerce')

        # Filtrar por período (exemplo: últimos 12 meses)
        end_date = datetime.now()
        start_date = end_date - pd.DateOffset(months=12)

        df_filtered = df_processado[(df_processado['Data de Vencimento'] >= start_date) & (df_processado['Data de Vencimento'] <= end_date)]

        # Gráfico de barras: Contas a Pagar vs. Receber por Mês
        df_monthly = df_filtered.groupby(df_filtered['Data de Vencimento'].dt.to_period('M'))['Valor Original'].sum().reset_index()
        df_monthly['Data de Vencimento'] = df_monthly['Data de Vencimento'].astype(str)

        fig = px.bar(df_monthly, x='Data de Vencimento', y='Valor Original', title='Contas por Mês')
        st.plotly_chart(fig, use_container_width=True)

        # Gráfico de pizza: Status das Contas
        df_status = df_processado['Status'].value_counts().reset_index()
        df_status.columns = ['Status', 'Count']
        fig_status = px.pie(df_status, values='Count', names='Status', title='Status das Contas')
        st.plotly_chart(fig_status, use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        st.info("Por favor, verifique se o arquivo Excel está no formato esperado e se as colunas necessárias existem.")

