import pandas as pd
import numpy as np
from load_and_filter import load_and_filter_data
from b3_scraper import get_b3_rates_uc

def calculate_mtm(df):
    """
    Calculates the MtM result using the provided formula and B3 data.
    """
    df['preco_b3_referencia'] = np.nan
    df['preco_b3_anterior'] = np.nan
    df['resultado_correto'] = np.nan
    df['validacao_b3'] = 'Falhou'

    unique_dates = pd.unique(df[['data_referencia', 'data_anterior']].values.ravel('K'))
    all_rates = {}
    for date_ns in unique_dates:
        ref_date = pd.to_datetime(date_ns).date()
        rates_df = get_b3_rates_uc(ref_date)
        if rates_df is not None:
            all_rates[ref_date] = rates_df

    for index, row in df.iterrows():
        ref_date = pd.to_datetime(row['data_referencia']).date()
        ant_date = pd.to_datetime(row['data_anterior']).date()
        n_dias = int(row['n_dias_corridos'])
        n_dias_ant = int(row['n_dias_corridos_anterior'])

        preco_ref_b3 = np.nan
        preco_ant_b3 = np.nan

        if ref_date in all_rates and n_dias in all_rates[ref_date].index:
            preco_ref_b3 = all_rates[ref_date].loc[n_dias, 'taxas252']
            df.loc[index, 'preco_b3_referencia'] = preco_ref_b3 * 100

        if ant_date in all_rates and n_dias_ant in all_rates[ant_date].index:
            preco_ant_b3 = all_rates[ant_date].loc[n_dias_ant, 'taxas252']
            df.loc[index, 'preco_b3_anterior'] = preco_ant_b3 * 100

        if pd.notna(preco_ref_b3) and pd.notna(preco_ant_b3):
            df.loc[index, 'validacao_b3'] = 'Sucesso'

            fator_compra_venda = -1 if row['comprado/vendido'] == 'C' else 1
            pu_ref = 100000 / ((1 + preco_ref_b3) ** (row['n_dias_uteis'] / 252))
            pu_ant = 100000 / ((1 + preco_ant_b3) ** (row['n_dias_uteis_anterior'] / 252))
            fator_cdi = row['fator_cdi'] if pd.notna(row['fator_cdi']) else 1

            resultado = fator_compra_venda * row['quantidade'] * (pu_ref - pu_ant * fator_cdi)
            df.loc[index, 'resultado_correto'] = resultado
        else:
            # Se não houver dados da B3, não podemos calcular o resultado correto
            df.loc[index, 'resultado_correto'] = 'Dados da B3 indisponíveis'


    return df

if __name__ == '__main__':
    filtered_df = load_and_filter_data('case.xlsx')

    final_df = calculate_mtm(filtered_df.copy())

    # Adiciona a coluna de verificação de erro
    final_df['status_validacao'] = 'OK'
    mask = pd.to_numeric(final_df['resultado_correto'], errors='coerce').notna()
    diff = (final_df.loc[mask, 'resultado'] - final_df.loc[mask, 'resultado_correto']).abs().round(3)
    final_df.loc[mask & (diff > 0), 'status_validacao'] = 'ERRO'


    output_columns = [
        'id_trader', 'ativo', 'data_referencia', 'preco_data_referencia', 'preco_b3_referencia',
        'data_anterior', 'preco_data_anterior', 'preco_b3_anterior', 'resultado', 'resultado_correto', 'validacao_b3', 'status_validacao'
    ]

    final_df[output_columns].to_excel('validacao_mtm_final.xlsx', index=False)
    print("Relatório 'validacao_mtm_final.xlsx' gerado com sucesso.")
