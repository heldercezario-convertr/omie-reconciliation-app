import streamlit as st
import pandas as pd
from process_omie_data import process_omie_spreadsheet
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(layout="wide", page_title="Conciliação OMIE Convertr", page_icon="💰")

# Paleta de cores da Convertr (baseada no site e sua preferência)
COLOR_PRIMARY = "#7650fd"  # Roxo principal
COLOR_SECONDARY = "#a68cff" # Roxo claro
COLOR_SUCCESS = "#51cf66"  # Verde
COLOR_WARNING = "#ffd43b"  # Amarelo
COLOR_DANGER = "#ff6b6b"   # Vermelho
COLOR_NEUTRAL = "#f0f2f6"  # Cinza claro
COLOR_TEXT = "#333333"    # Cor padrão para texto

# CSS personalizado para melhorar a aparência e aplicar a identidade visual
st.markdown(f"""
<style>
    .reportview-container .main .block-container{{
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }}
    .metric-card {{
        background-color: {COLOR_NEUTRAL};
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid {COLOR_PRIMARY};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }}
    .stMetric > label {{
        font-size: 14px !important;
        color: {COLOR_PRIMARY} !important;
        font-weight: bold !important;
    }}
    .stMetric > div {{
        font-size: 24px !important;
        font-weight: bold !important;
        color: {COLOR_TEXT};
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {COLOR_PRIMARY};
    }}
    .stButton>button {{
        background-color: {COLOR_PRIMARY};
        color: white;
        border-radius: 0.5rem;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: bold;
    }}
    .stButton>button:hover {{
        background-color: {COLOR_SECONDARY};
        color: white;
    }}
    .stFileUploader label {{
        color: {COLOR_PRIMARY};
        font-weight: bold;
    }}
    .stFileUploader div[data-testid="stFileUploaderDropzone"] {{
        border: 2px dashed {COLOR_SECONDARY};
        border-radius: 0.5rem;
        padding: 2rem;
    }}
    .stFileUploader div[data-testid="stFileUploaderDropzone"] svg {{
        color: {COLOR_PRIMARY};
    }}
    .stPlotlyChart {{
        border: 1px solid {COLOR_NEUTRAL};
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        padding: 0.5rem;
    }}
</style>
""", unsafe_allow_html=True)

# Adicionar o logo da Convertr
logo_path = "/home/ubuntu/upload/MarcaVertical(Positivo).png"
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_column_width=True)
else:
    st.sidebar.warning("Logo da Convertr não encontrado. Verifique o caminho.")

st.title("💰 Conciliação Financeira OMIE - Convertr")
st.markdown("**Sistema de Conciliação Automática para Gestão Financeira**")
st.markdown("---")

st.sidebar.header("📁 Upload da Planilha OMIE")
st.sidebar.markdown("Faça o upload da planilha **\"Contas por Período.xlsx\"** extraída do sistema OMIE.")

uploaded_file = st.sidebar.file_uploader(
    "Arraste e solte sua planilha aqui", 
    type=["xlsx"],
    help="Selecione o arquivo \"Contas por Período.xlsx\" do OMIE"
)

if uploaded_file is not None:
    st.sidebar.success("✅ Planilha carregada com sucesso!")
    
    # Salvar o arquivo temporariamente
    temp_file_path = "temp_omie_file.xlsx"
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Processar os dados
    with st.spinner("Processando dados da planilha..."):
        full_data, summary_data, pending_items = process_omie_spreadsheet(temp_file_path)

    if full_data is not None and not full_data.empty:
        st.header("📊 Resumo Executivo")
        
        # Novas métricas de pendências
        receber_atrasado = pending_items[(pending_items["Tipo_Transacao"] == "Contas a Receber") & (pending_items["Situacao_Pendente"] == "A Receber (Atrasado)")]["A_Pagar_ou_Receber"].sum()
        receber_futuro = pending_items[(pending_items["Tipo_Transacao"] == "Contas a Receber") & (pending_items["Situacao_Pendente"] == "A Receber (Futuro)")]["A_Pagar_ou_Receber"].sum()
        pagar_atrasado = pending_items[(pending_items["Tipo_Transacao"] == "Contas a Pagar") & (pending_items["Situacao_Pendente"] == "A Pagar (Atrasado)")]["A_Pagar_ou_Receber"].sum()
        pagar_futuro = pending_items[(pending_items["Tipo_Transacao"] == "Contas a Pagar") & (pending_items["Situacao_Pendente"] == "A Pagar (Futuro)")]["A_Pagar_ou_Receber"].sum()
        
        total_recebido = full_data[(full_data["Tipo_Transacao"] == "Contas a Receber") & (full_data["Status_Conciliacao"] == "Recebido/Pago")]["Pago_ou_Recebido"].sum()
        total_pago = full_data[(full_data["Tipo_Transacao"] == "Contas a Pagar") & (full_data["Status_Conciliacao"] == "Recebido/Pago")]["Pago_ou_Recebido"].sum()
        saldo_liquido_pendente = receber_atrasado + receber_futuro - pagar_atrasado - pagar_futuro

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                label="💰 A Receber (Atrasado)",
                value=f"R$ {receber_atrasado:,.2f}",
                delta=None
            )
        with col2:
            st.metric(
                label="⏳ A Receber (Futuro)",
                value=f"R$ {receber_futuro:,.2f}",
                delta=None
            )
        with col3:
            st.metric(
                label="🚨 A Pagar (Atrasado)",
                value=f"R$ {abs(pagar_atrasado):,.2f}",
                delta=None
            )
        with col4:
            st.metric(
                label="🗓️ A Pagar (Futuro)",
                value=f"R$ {abs(pagar_futuro):,.2f}",
                delta=None
            )

        st.markdown("###") # Espaçamento
        col_total_recebido, col_total_pago, col_saldo_liquido = st.columns(3)
        with col_total_recebido:
            st.metric(
                label="✅ Total Recebido",
                value=f"R$ {total_recebido:,.2f}",
                delta=None
            )
        with col_total_pago:
            st.metric(
                label="💸 Total Pago",
                value=f"R$ {total_pago:,.2f}",
                delta=None
            )
        with col_saldo_liquido:
            st.metric(
                label="📊 Saldo Líquido Pendente",
                value=f"R$ {saldo_liquido_pendente:,.2f}",
                delta=None
            )

        # Gráficos
        st.header("📈 Análise Visual")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza - Distribuição por Status de Conciliação
            # Agrupar para o gráfico de pizza
            pie_data = summary_data.groupby("Status_Conciliacao")["Total_Valor_Liquido"].sum().reset_index()
            fig_pie = px.pie(
                pie_data, 
                values='Total_Valor_Liquido', 
                names='Status_Conciliacao',
                title="Distribuição por Status de Conciliação",
                color_discrete_map={'Pendente': COLOR_DANGER, 'Recebido/Pago': COLOR_SUCCESS},
                hole=0.3 # Para um visual de donut
            )
            fig_pie.update_traces(marker=dict(line=dict(color='#FFFFFF', width=2)))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Gráfico de barras - Valores por Tipo de Transação e Situação Pendente
            # Filtrar apenas pendentes para este gráfico
            bar_data = pending_items.groupby(["Tipo_Transacao", "Situacao_Pendente"])["A_Pagar_ou_Receber"].sum().reset_index()
            fig_bar = px.bar(
                bar_data,
                x='Tipo_Transacao',
                y='A_Pagar_ou_Receber',
                color='Situacao_Pendente',
                title="Valores Pendentes por Tipo e Situação",
                color_discrete_map={
                    'A Receber (Atrasado)': COLOR_DANGER,
                    'A Receber (Futuro)': COLOR_WARNING,
                    'A Pagar (Atrasado)': COLOR_DANGER,
                    'A Pagar (Futuro)': COLOR_WARNING
                },
                barmode='group'
            )
            fig_bar.update_layout(xaxis_title="Tipo de Transação", yaxis_title="Valor Pendente")
            st.plotly_chart(fig_bar, use_container_width=True)

        # Resumo da Conciliação
        st.header("📋 Resumo da Conciliação")
        st.dataframe(summary_data, use_container_width=True)

        # Itens Pendentes
        st.header("⚠️ Itens Pendentes - Ação Necessária")
        
        if len(pending_items) > 0:
            # Filtros para itens pendentes
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_filtro = st.selectbox(
                    "Filtrar por tipo:",
                    ["Todos"] + list(pending_items["Tipo_Transacao"].unique())
                )
            with col2:
                situacao_vencimento_filtro = st.selectbox(
                    "Filtrar por situação de vencimento:",
                    ["Todas"] + list(pending_items["Situação_do_Vencimento"].unique())
                )
            with col3:
                situacao_pendente_filtro = st.selectbox(
                    "Filtrar por status de pendência:",
                    ["Todos"] + list(pending_items["Situacao_Pendente"].unique())
                )
            
            # Aplicar filtros
            filtered_pending = pending_items.copy()
            if tipo_filtro != "Todos":
                filtered_pending = filtered_pending[filtered_pending["Tipo_Transacao"] == tipo_filtro]
            if situacao_vencimento_filtro != "Todos":
                filtered_pending = filtered_pending[filtered_pending["Situação_do_Vencimento"] == situacao_vencimento_filtro]
            if situacao_pendente_filtro != "Todos":
                filtered_pending = filtered_pending[filtered_pending["Situacao_Pendente"] == situacao_pendente_filtro]
            
            st.dataframe(filtered_pending, use_container_width=True)
            
            # Botão de download para itens pendentes
            csv_pendentes = filtered_pending.to_csv(index=False)
            st.download_button(
                label="📥 Baixar Lista de Pendências (CSV)",
                data=csv_pendentes,
                file_name=f"pendencias_omie_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.csv",
                mime="text/csv"
            )
        else:
            st.success("🎉 Não há itens pendentes! Todas as contas estão em dia.")

        # Dados Completos (em uma aba expansível)
        with st.expander("📊 Ver Dados Completos da Planilha"):
            st.dataframe(full_data, use_container_width=True)
            
            # Botão de download para dados completos
            csv_completo = full_data.to_csv(index=False)
            st.download_button(
                label="📥 Baixar Dados Completos (CSV)",
                data=csv_completo,
                file_name=f"dados_completos_omie_{datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.csv",
                mime="text/csv"
            )

    else:
        st.error("❌ Erro ao processar a planilha. Verifique o formato e tente novamente.")
        st.info("💡 Certifique-se de que o arquivo é uma planilha Excel (.xlsx) válida do OMIE.")

else:
    st.info("👆 Por favor, faça o upload da planilha **\"Contas por Período.xlsx\"** na barra lateral para iniciar a conciliação.")
    
    # Instruções de uso
    st.markdown("""
    ### 📖 Como usar esta ferramenta:
    
    1. **Extrair dados do OMIE**: Acesse o sistema OMIE e gere o relatório "Contas por Período"
    2. **Fazer upload**: Use a barra lateral para carregar o arquivo .xlsx
    3. **Analisar resultados**: Visualize os KPIs, gráficos e listas de pendências
    4. **Tomar ações**: Use a lista de pendências para cobrar clientes ou efetuar pagamentos
    5. **Exportar dados**: Baixe as listas em CSV para uso em outras ferramentas
    
    ### 🎯 Benefícios:
    - ✅ **Automação completa** do processo de conciliação
    - 📊 **Visualizações claras** para tomada de decisão
    - ⚡ **Processamento rápido** de grandes volumes de dados
    - 📥 **Exportação fácil** para planilhas e relatórios
    """)

