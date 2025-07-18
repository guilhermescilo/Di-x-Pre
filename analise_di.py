import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO
from datetime import date
import urllib3

# Desativa o aviso de request não seguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_b3_di_rates(target_date):
    """
    Busca as taxas de DI futuro da B3 para uma data específica.
    """
    mes = target_date.month
    dia = target_date.day
    if target_date.month < 10:
        mes = '0' + str(target_date.month)
    if target_date.day < 10:
        dia = '0' + str(target_date.day)
    
    dt_barra = f'{dia}/{mes}/{target_date.year}'
    dt_corrida = f'{target_date.year}{mes}{dia}'
    headers = {
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
    }
    
    link = f'https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data={dt_barra}&Data1={dt_corrida}&slcTaxa=PRE'
    
    try:
        page = requests.get(link, headers=headers, verify=False)
        soup = BeautifulSoup(page.content, 'html.parser')
        texto = soup.find_all('td')
        
        dias, taxas252 = [], []
        tabelas = ["['tabelaConteudo1']", "['tabelaConteudo2']"]
        
        start_index = -1
        for i in range(len(texto)):
            if str(texto[i].get('class')) in tabelas:
                start_index = i
                break
        
        if start_index != -1:
            for i in range(start_index, len(texto), 3):
                if i + 2 < len(texto) and str(texto[i].get('class')) in tabelas:
                    dias_str = texto[i].text.replace('\r\n','').replace(',','.').replace(' ','')
                    taxas252_str = texto[i+1].text.replace('\r\n','').replace(',','.').replace(' ','')
                    
                    dias.append(int(dias_str))
                    taxas252.append(float(taxas252_str))
                    
        return pd.DataFrame({'dias_corridos_b3': dias, 'taxa_252_b3': taxas252})
        
    except Exception as e:
        print(f"Erro ao buscar dados da B3: {e}")
        return None

def main():
    # Dados das planilhas
    estoque_data = """data_referencia	data_anterior	data_operacao	id_trader	nome_produto	quantidade	comprado/vendido	ativo	data_vencimento	n_dias_uteis	n_dias_uteis_anterior	n_dias_corridos	n_dias_corridos_anterior	preco_data_referencia	preco_data_anterior	fator_cdi	resultado
09/jul/25	09/jul/25	08/jul/25	11	Estoque moeda	8000	C	USDBRL						5,57	5,46		880,00
09/jul/25	09/jul/25	09/jul/25	4	Estoque moeda	50000	C	USDBRL						5,57	5,46		5.500,00
09/jul/25	08/jul/25	30/abr/25	10	Ação Local	1000	C	ITUB4						36,37	37,14		-770,00
09/jul/25	08/jul/25	09/mai/25	2	Ação Local	500	C	ITUB4						36,37	37,14		-385,00
08/jul/25	07/jul/25	08/jul/25	11	Estoque moeda	8000	C	USDBRL						5,46	5,44		140,00
08/jul/25	07/jul/25	30/abr/25	10	Ação Local	1000	C	ITUB4						37,14	37,23		-90,00
08/jul/25	07/jul/25	09/mai/25	2	Ação Local	500	C	ITUB4						37,14	37,23		-45,00
08/jul/25	07/jul/25	06/jan/25	9	Futuro de DI	5	C	DI1F29	02/01/2029	873	874	1.274	1.275	13,31	13,31	1,000551	17,93
08/jul/25	07/jul/25	10/jun/25	4	Futuro de DI	20	V	DI1F29	02/01/2029	873	874	1.274	1.275	13,31	13,31	1,000551	-71,74
08/jul/25	07/jul/25	15/abr/25	8	Futuro de DI	20	C	DI1F29	02/01/2029	873	874	1.274	1.275	13,31	13,31	1,000551	71,74
08/jul/25	07/jul/25	15/abr/25	7	Futuro de DI	5	V	DI1F29	02/01/2029	873	874	1.274	1.275	13,31	13,31	1,000551	-17,93
08/jul/25	07/jul/25	18/fev/25	6	Futuro de DI	10	V	DI1F31	02/01/2031	1.374	1.375	2.004	2.005	13,42	13,40	1,000551	-510,43
08/jul/25	07/jul/25	17/fev/25	1	Futuro de DI	5	C	DI1F27	04/01/2027	374	375	545	546	14,21	14,20	1,000551	63,31
08/jul/25	07/jul/25	14/fev/25	10	Futuro de DI	15	C	DI1F26	02/01/2026	125	126	178	179	14,92	14,92	1,000551	-0,97
08/jul/25	07/jul/25	14/fev/25	5	Futuro de DI	30	V	DI1F26	02/01/2026	125	126	178	179	14,92	14,92	1,000551	1,93
08/jul/25	07/jul/25	13/ago/24	3	Futuro de DI	20	V	DI1N26	01/07/2026	247	248	358	359	14,70	14,71	1,000551	137,92
08/jul/25	07/jul/25	05/abr/23	2	Futuro de DI	20	C	DI1N26	01/07/2026	247	248	358	359	14,70	14,71	1,000551	-137,92
07/jul/25	04/jul/25	30/abr/25	10	Ação Local	1000	C	ITUB4						37,23	37,73		-500,00
07/jul/25	04/jul/25	09/mai/25	2	Ação Local	500	C	ITUB4						37,23	37,73		-250,00
07/jul/25	04/jul/25	06/jan/25	9	Futuro de DI	5	C	DI1F29	02/01/2029	874	875	1.275	1.278	13,31	13,21	1,000551	1.013,27
07/jul/25	04/jul/25	10/jun/25	4	Futuro de DI	20	V	DI1F29	02/01/2029	874	875	1.275	1.278	13,31	13,21	1,000551	-4.053,09
07/jul/25	04/jul/25	15/abr/25	8	Futuro de DI	20	C	DI1F29	02/01/2029	874	875	1.275	1.278	13,31	13,21	1,000551	4.053,09
07/jul/25	04/jul/25	15/abr/25	7	Futuro de DI	5	V	DI1F29	02/01/2029	874	875	1.275	1.278	13,31	13,21	1,000551	-1.013,27
07/jul/25	04/jul/25	18/fev/25	6	Futuro de DI	10	V	DI1F31	02/01/2031	1.375	1.376	2.005	2.008	13,40	13,27	1,000551	-3.189,94
07/jul/25	04/jul/25	17/fev/25	1	Futuro de DI	5	C	DI1F27	04/01/2027	375	376	546	549	14,20	14,16	1,000551	224,51
07/jul/25	04/jul/25	14/fev/25	10	Futuro de DI	15	C	DI1F26	02/01/2026	126	127	179	182	14,92	14,91	1,000551	60,40
07/jul/25	04/jul/25	14/fev/25	5	Futuro de DI	30	V	DI1F26	02/01/2026	126	127	179	182	14,92	14,91	1,000551	-120,80
07/jul/25	04/jul/25	13/ago/24	3	Futuro de DI	20	V	DI1N26	01/07/2026	248	249	359	362	14,71	14,68	1,000551	-463,13
07/jul/25	04/jul/25	05/abr/23	2	Futuro de DI	20	C	DI1N26	01/07/2026	248	249	359	362	14,71	14,68	1,000551	463,13
"""
    traders_data = """id_trader	nome_trader
1	Augusto
2	Bernardo
3	Ricardo
4	Marcio
5	Jessica
6	Paula
7	Kim
8	Joao
9	Aline
10	Otto
11	Raquel
"""
    
    # Carregar dados
    df_estoque = pd.read_csv(StringIO(estoque_data), sep='\t')
    df_traders = pd.read_csv(StringIO(traders_data), sep='\t')
    
    # Filtrar Futuro de DI
    df_di = df_estoque[df_estoque['nome_produto'] == 'Futuro de DI'].copy()
    
    # Obter dados da B3 (usando uma data fixa para garantir resultados)
    target_date = date(2024, 7, 17)
    df_b3 = get_b3_di_rates(target_date)
    
    if df_b3 is None:
        print("Não foi possível continuar a análise sem os dados da B3.")
        return
        
    # Juntar os dados
    df_merged = pd.merge(df_di, df_b3, left_on='n_dias_corridos', right_on='dias_corridos_b3', how='left')
    
    # Identificar operações com problemas
    df_merged['preco_divergente'] = df_merged['preco_data_referencia'] != df_merged['taxa_252_b3']
    
    # Calcular resultado correto
    df_merged['resultado_correto'] = (df_merged['preco_data_referencia'] - df_merged['preco_data_anterior']) * df_merged['quantidade'] * 1000
    df_merged.loc[df_merged['comprado/vendido'] == 'V', 'resultado_correto'] *= -1
    
    # Gerar relatório
    report = df_merged[df_merged['preco_divergente']]
    report = pd.merge(report, df_traders, on='id_trader')
    
    report_final = report[['data_referencia', 'nome_trader', 'ativo', 'preco_data_referencia', 'taxa_252_b3', 'resultado', 'resultado_correto']]
    
    print("\nRelatório de Operações com Divergência:")
    print(report_final)
    
    # Salvar relatório
    report_final.to_csv('relatorio_divergencias.csv', index=False)
    print("\nRelatório salvo em 'relatorio_divergencias.csv'")

if __name__ == '__main__':
    main()
