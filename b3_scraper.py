import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import time

def get_b3_rates_uc(ref_date):
    """
    Scrapes B3 website for DI rates for a given reference date using undetected_chromedriver.
    """
    dt_str = ref_date.strftime('%d/%m/%Y')
    dt_corrida = ref_date.strftime('%Y%m%d')
    link = f'http://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/TxRef1.asp?Data={dt_str}&Data1={dt_corrida}&slcTaxa=PRE'

    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        driver = uc.Chrome(options=options)
        driver.get(link)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        texto = soup.find_all('td')

        dias, taxas252 = [], []
        tabelas = ["tabelaConteudo1", "tabelaConteudo2"]

        for i in range(0, len(texto), 3):
            if texto[i].has_attr('class') and any(c in texto[i]['class'] for c in tabelas):
                try:
                    if i <= len(texto) - 2:
                        dias.append(int(texto[i].text.strip().replace(',','.')))
                        taxas252.append(float(texto[i+1].text.strip().replace(',','.')) / 100)
                except (ValueError, IndexError) as e:
                    print(f"Skipping a row due to parsing error: {e}")
                    continue

        if not dias:
            print(f"No data found or parsed for {dt_str}")
            return None

        return pd.DataFrame({'taxas252': taxas252}, index=dias)

    except Exception as e:
        print(f"An error occurred while scraping {dt_str}: {e}")
        if 'driver' in locals() and driver:
            driver.quit()
        return None

if __name__ == '__main__':
    from load_and_filter import load_and_filter_data

    filtered_df = load_and_filter_data('case.xlsx')
    unique_dates = filtered_df['data_referencia'].unique()

    all_rates = {}
    for date_ns in unique_dates:
        ref_date = pd.to_datetime(date_ns).date()
        print(f"Attempting to scrape rates for {ref_date.strftime('%Y-%m-%d')}")
        rates_df = get_b3_rates_uc(ref_date)

        if rates_df is not None:
            all_rates[ref_date] = rates_df
            print(f"Successfully scraped rates for {ref_date.strftime('%Y-%m-%d')}")
            print(rates_df.head())
        else:
            print(f"Failed to scrape rates for {ref_date.strftime('%Y-%m-%d')}")

    if not all_rates:
        print("No rates were scraped.")
