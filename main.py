import pandas as pd
import numpy as np
from load_and_filter import load_and_filter_data
from b3_scraper import get_b3_rates_uc

def compare_prices_and_identify_problems_revised(df, all_rates):
    """
    Compares prices from the dataframe with B3 rates using n_dias_corridos.
    """
    df['n_dias_corridos'] = df['n_dias_corridos'].astype(int)
    df['n_dias_corridos_anterior'] = df['n_dias_corridos_anterior'].astype(int)
    df['problema'] = False
    df['preco_b3_referencia'] = None
    df['preco_b3_anterior'] = None

    for index, row in df.iterrows():
        ref_date = pd.to_datetime(row['data_referencia']).date()
        ant_date = pd.to_datetime(row['data_anterior']).date()
        n_dias = row['n_dias_corridos']
        n_dias_ant = row['n_dias_corridos_anterior']

        problema_referencia = True
        problema_anterior = True

        # Check a data de referência
        if ref_date in all_rates and n_dias in all_rates[ref_date].index:
            preco_b3_ref = all_rates[ref_date].loc[n_dias, 'taxas252'] * 100
            df.loc[index, 'preco_b3_referencia'] = preco_b3_ref
            if np.isclose(row['preco_data_referencia'], preco_b3_ref, atol=1e-9):
                problema_referencia = False

        # Check a data anterior
        if ant_date in all_rates and n_dias_ant in all_rates[ant_date].index:
            preco_b3_ant = all_rates[ant_date].loc[n_dias_ant, 'taxas252'] * 100
            df.loc[index, 'preco_b3_anterior'] = preco_b3_ant
            if np.isclose(row['preco_data_anterior'], preco_b3_ant, atol=1e-9):
                problema_anterior = False

        if problema_referencia or problema_anterior:
            df.loc[index, 'problema'] = True

    return df

def calculate_correct_mtm_revised(df):
    """
    Calculates the correct MtM result for problematic operations.
    """
    df['resultado_correto'] = None

    for index, row in df.iterrows():
        if row['problema']:
            preco_ref = row['preco_b3_referencia'] if pd.notna(row['preco_b3_referencia']) else row['preco_data_referencia']
            preco_ant = row['preco_b3_anterior'] if pd.notna(row['preco_b3_anterior']) else row['preco_data_anterior']

            resultado = (preco_ref - preco_ant) * row['quantidade']
            if row['comprado/vendido'] == 'Vendido':
                resultado *= -1
            df.loc[index, 'resultado_correto'] = resultado

    return df

if __name__ == '__main__':
    filtered_df = load_and_filter_data('case.xlsx')

    unique_dates = pd.unique(filtered_df[['data_referencia', 'data_anterior']].values.ravel('K'))
    all_rates = {}
    for date_ns in unique_dates:
        ref_date = pd.to_datetime(date_ns).date()
        rates_df = get_b3_rates_uc(ref_date)
        if rates_df is not None:
            all_rates[ref_date] = rates_df

    if all_rates:
        df_with_problems = compare_prices_and_identify_problems_revised(filtered_df, all_rates)
        df_with_mtm = calculate_correct_mtm_revised(df_with_problems)

        problematic_ops = df_with_mtm[df_with_mtm['problema']].copy()

        output_columns = [
            'id_trader', 'ativo', 'data_referencia', 'preco_data_referencia', 'preco_b3_referencia',
            'data_anterior', 'preco_data_anterior', 'preco_b3_anterior', 'resultado', 'resultado_correto'
        ]

        problematic_ops[output_columns].to_excel('validacao_mtm.xlsx', index=False)
        print("Relatório 'validacao_mtm.xlsx' gerado com sucesso.")

    else:
        print("Não foi possível obter as taxas da B3. A comparação não pode ser realizada.")
