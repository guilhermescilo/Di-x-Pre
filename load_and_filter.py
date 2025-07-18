import pandas as pd

def load_and_filter_data(file_path):
    """
    Loads data from an Excel file and filters for 'Futuro de DI' products.
    """
    df = pd.read_excel(file_path)
    df_futuro_di = df[df['nome_produto'] == 'Futuro de DI'].copy()
    return df_futuro_di

if __name__ == '__main__':
    filtered_df = load_and_filter_data('case.xlsx')
    print("Dados filtrados com sucesso:")
    print(filtered_df.head())
