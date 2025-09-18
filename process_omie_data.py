import pandas as pd
from datetime import datetime

def process_omie_spreadsheet(file_path):
    try:
        # Tentar ler a planilha, ignorando as primeiras linhas até encontrar o cabeçalho
        df_raw = pd.read_excel(file_path, header=None)

        # Encontrar a linha do cabeçalho (geralmente a que contém 'Cliente ou Fornecedor (Nome Fantasia)')
        header_row_index = None
        for i in range(min(10, len(df_raw))): # Limitar a busca às primeiras 10 linhas
            # Procurar pelo nome original da coluna no DataFrame bruto
            if 'Cliente ou Fornecedor (Nome Fantasia)' in df_raw.iloc[i].astype(str).values:
                header_row_index = i
                break
        
        if header_row_index is None:
            raise ValueError("Não foi possível encontrar a linha do cabeçalho. Verifique o formato da planilha.")

        # Ler a planilha novamente, definindo o cabeçalho correto
        df = pd.read_excel(file_path, header=header_row_index)

        # Remover linhas totalmente vazias que podem vir após o cabeçalho
        df.dropna(how='all', inplace=True)

        # Limpar nomes das colunas: remover espaços, caracteres especiais e acentuação
        def clean_col_name(col):
            col = str(col).strip().replace(' ', '_').replace('/', '_').replace('-', '_')
            col = ''.join(c for c in col if c.isalnum() or c == '_')
            col = col.replace('__', '_').strip('_')
            return col

        df.columns = [clean_col_name(col) for col in df.columns]

        # Garantir que as colunas essenciais existam
        required_columns = [
            'Tipo',
            'Situação_do_Vencimento',
            'Conciliado',
            'Valor_da_Conta',
            'Pago_ou_Recebido',
            'A_Pagar_ou_Receber',
            'Data_de_Vencimento_completa',
            'Última_Data_de_Pagto_ou_Recbto_completa',
            'Cliente_ou_Fornecedor_Nome_Fantasia'
        ]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Coluna essencial '{col}' não encontrada na planilha.")

        # Converter tipos de dados
        df['Data_de_Vencimento_completa'] = pd.to_datetime(df['Data_de_Vencimento_completa'], errors='coerce')
        df['Última_Data_de_Pagto_ou_Recbto_completa'] = pd.to_datetime(df['Última_Data_de_Pagto_ou_Recbto_completa'], errors='coerce')
        df['Data_de_Emissão_completa'] = pd.to_datetime(df['Data_de_Emissão_completa'], errors='coerce')
        df['Data_de_Previsão_completa'] = pd.to_datetime(df['Data_de_Previsão_completa'], errors='coerce')

        # Tratar valores numéricos (remover R$, pontos e vírgulas para converter para float)
        def clean_numeric_value(value):
            if isinstance(value, str):
                # Remover R$, pontos de milhar e substituir vírgula decimal por ponto
                cleaned_value = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
                try:
                    return float(cleaned_value)
                except ValueError:
                    return None # Retorna None para valores que não podem ser convertidos
            return float(value)

        df['Valor_da_Conta'] = df['Valor_da_Conta'].apply(clean_numeric_value)
        df['Pago_ou_Recebido'] = df['Pago_ou_Recebido'].apply(clean_numeric_value)
        df['A_Pagar_ou_Receber'] = df['A_Pagar_ou_Receber'].apply(clean_numeric_value)
        
        # Criar coluna de status de conciliação
        # Uma transação é 'Recebido/Pago' se o 'A_Pagar_ou_Receber' for 0 OU se 'Conciliado' for 'Sim'
        # Corrigido: Usar 'Pago_ou_Recebido' para determinar se foi pago/recebido
        df['Status_Conciliacao'] = df.apply(lambda row: 'Recebido/Pago' if (row['Pago_ou_Recebido'] > 0 or row['Conciliado'] == 'Sim') else 'Pendente', axis=1)

        # Criar coluna de tipo de transação mais amigável
        df['Tipo_Transacao'] = df['Tipo'].map({'1. Contas a Receber': 'Contas a Receber', '2. Contas a Pagar': 'Contas a Pagar'})

        # Classificar pendências em Atrasado ou Futuro
        today = datetime.now().date()
        df['Situacao_Pendente'] = ''
        
        # Apenas para itens pendentes
        pending_mask = df['Status_Conciliacao'] == 'Pendente'

        # Contas a Receber Pendentes
        receber_pendente_mask = pending_mask & (df['Tipo_Transacao'] == 'Contas a Receber')
        df.loc[receber_pendente_mask & (df['Data_de_Vencimento_completa'].dt.date < today), 'Situacao_Pendente'] = 'A Receber (Atrasado)'
        df.loc[receber_pendente_mask & (df['Data_de_Vencimento_completa'].dt.date >= today), 'Situacao_Pendente'] = 'A Receber (Futuro)'

        # Contas a Pagar Pendentes
        pagar_pendente_mask = pending_mask & (df['Tipo_Transacao'] == 'Contas a Pagar')
        df.loc[pagar_pendente_mask & (df['Data_de_Vencimento_completa'].dt.date < today), 'Situacao_Pendente'] = 'A Pagar (Atrasado)'
        df.loc[pagar_pendente_mask & (df['Data_de_Vencimento_completa'].dt.date >= today), 'Situacao_Pendente'] = 'A Pagar (Futuro)'

        # Preencher Situacao_Pendente para itens não pendentes (para evitar NaN)
        df.loc[df['Status_Conciliacao'] == 'Recebido/Pago', 'Situacao_Pendente'] = 'Não Pendente'

        # Resumo dos dados para KPIs e gráficos
        # Corrigido: Usar 'Pago_ou_Recebido' para 'Recebido/Pago' e 'A_Pagar_ou_Receber' para 'Pendente'
        summary_data_recebido_pago = df[df['Status_Conciliacao'] == 'Recebido/Pago'].groupby(['Tipo_Transacao', 'Status_Conciliacao']).agg(
            Total_Valor_Liquido=('Pago_ou_Recebido', 'sum'),
            Quantidade_Transacoes=('Tipo_Transacao', 'count')
        ).reset_index()

        summary_data_pendente = df[df['Status_Conciliacao'] == 'Pendente'].groupby(['Tipo_Transacao', 'Status_Conciliacao']).agg(
            Total_Valor_Liquido=('A_Pagar_ou_Receber', 'sum'),
            Quantidade_Transacoes=('Tipo_Transacao', 'count')
        ).reset_index()

        summary_data = pd.concat([summary_data_recebido_pago, summary_data_pendente])
        
        # Filtrar itens pendentes
        pending_items = df[df['Status_Conciliacao'] == 'Pendente'].copy()
        
        return df, summary_data, pending_items

    except Exception as e:
        print(f'Erro ao processar a planilha: {e}')
        return None, None, None

if __name__ == '__main__':
    file_path = '/home/ubuntu/upload/Contasporperiodo.xlsx'
    full_data, summary_data, pending_data = process_omie_spreadsheet(file_path)

    if full_data is not None:
        print("\n--- Resumo da Conciliação ---")
        print(summary_data.to_markdown(index=False))

        print("\n--- Itens Pendentes (Primeiras 10 linhas) ---")
        print(pending_data.head(10).to_markdown(index=False))

        print("\n--- Total de Itens Pendentes ---")
        print(f"Contas a Receber Pendentes: {pending_data[pending_data['Tipo_Transacao'] == 'Contas a Receber']['A_Pagar_ou_Receber'].sum():.2f}")
        print(f"Contas a Pagar Pendentes: {pending_data[pending_data['Tipo_Transacao'] == 'Contas a Pagar']['A_Pagar_ou_Receber'].sum():.2f}")

        # Salvar resultados para inspeção
        summary_data.to_csv('conciliation_summary.csv', index=False)
        pending_data.to_csv('pending_items.csv', index=False)
        full_data.to_csv('processed_full_data.csv', index=False)
        print("Resultados salvos em conciliation_summary.csv, pending_items.csv e processed_full_data.csv")



