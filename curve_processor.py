import pandas as pd
import numpy as np
from datetime import date, timedelta
from workalendar.america import Brazil
from b3_scraper import get_b3_rates_uc

def get_last_business_day(start_date=None):
    """
    Returns the most recent business day.
    If start_date is None, starts from today.
    """
    cal = Brazil()
    if start_date is None:
        start_date = date.today()

    # If today is a holiday or weekend, we want the previous business day
    # workalendar's find_following_working_day doesn't go backwards easily without logic
    # simplest is to just check if today is working day, if not subtract one day until it is.

    current_date = start_date
    while not cal.is_working_day(current_date):
        current_date -= timedelta(days=1)

    return current_date

def fetch_latest_curve():
    """
    Attempts to scrape the curve starting from the latest business day.
    If scraping fails (data not published yet), moves backwards business day by day.
    Returns:
        tuple: (pd.DataFrame, date) or (None, None) if all attempts fail.
    """
    cal = Brazil()
    current_date = get_last_business_day()

    # Try up to 10 business days back
    for _ in range(10):
        print(f"Attempting to fetch curve for {current_date}")
        df = get_b3_rates_uc(current_date)
        if df is not None and not df.empty:
            return df, current_date

        # Go to previous business day
        current_date -= timedelta(days=1)
        while not cal.is_working_day(current_date):
            current_date -= timedelta(days=1)

    return None, None

def interpolate_curve(df):
    """
    Interpolates the B3 curve for all intermediate business days using Flat Forward 252.

    Formula:
    ((
      (1 + i_anterior/100)^(DU_anterior/252)
      *
      (
        ( (1 + i_posterior/100)^(DU_posterior/252) )
        /
        ( (1 + i_anterior/100)^(DU_anterior/252) )
      )^((DU - DU_anterior)/(DU_posterior - DU_anterior))
    )^(252/DU)
    - 1
    ) * 100

    Args:
        df (pd.DataFrame): DataFrame with index as Business Days (int) and column 'taxas252'.

    Returns:
        pd.DataFrame: Interpolated DataFrame.
    """
    if df is None or df.empty:
        return df

    # Ensure index is sorted and integer
    df.index = df.index.astype(int)
    df = df.sort_index()

    min_du = int(df.index.min())
    max_du = int(df.index.max())

    # Create the full index of integers
    full_index = range(min_du, max_du + 1)

    # Reindex to include all days, keeping existing values
    interpolated_df = df.reindex(full_index)

    # We need to fill the NaNs
    # It's easier to iterate through the known vertices to find gaps

    known_dus = df.index.tolist()

    for i in range(len(known_dus) - 1):
        du_ant = known_dus[i]
        du_post = known_dus[i+1]

        # If there are no gaps, continue
        if du_post == du_ant + 1:
            continue

        i_ant = df.loc[du_ant, 'taxas252']
        i_post = df.loc[du_post, 'taxas252']

        # Multiply by 100?
        # The scraper returns 'taxas252' as float (e.g. 0.05 for 5%).
        # The formula uses i_anterior/100. So if input is 5 (percent), we divide by 100.
        # But scraper output is already divided by 100?
        # Let's check b3_scraper.py:
        # taxas252.append(float(texto[i+1].text.strip().replace(',','.')) / 100)
        # So the dataframe contains 0.10 for 10%.
        # The formula provided by user: (1 + i_anterior/100).
        # This implies i_anterior is in percent (e.g. 10.0).
        # Since our dataframe has raw floats (0.10), we can just use (1 + val).
        # BUT wait.
        # Formula: ( (1 + i_anterior/100)^(DU_anterior/252) ... )
        # User explicitly wrote "i_anterior/100".
        # If my dataframe has 0.10, then "i_anterior" in the user's mind is 10.
        # So (1 + 0.10) is correct.
        # However, the formula ends with "* 100".
        # If I output the result as 10.0, I need to match the format.
        # The scraper returns 0.10.
        # If the user wants the result in the dataframe, usually we keep consistency.
        # The scraper returns decimals.
        # The formula returns Percent.
        # Let's look at the formula again:
        # ... - 1 ) * 100
        # This definitely returns a percentage (e.g. 10.5).
        # But the input dataframe `df` from scraper has decimals (e.g. 0.105).
        # I should probably return decimals to be consistent with the input dataframe format,
        # OR I should check if the user specifically requested the output in specific format.
        # "Armazena este dado em um dataframe que possa ser consultado por um outro código."
        # The formula explicitly has `* 100` at the end.
        # And expects `i/100` inside.
        # So if I plug in `val` (0.10) as `i/100`, that works: `(1 + val)`.
        # At the end, `... - 1` gives me the decimal rate.
        # The user formula says `... - 1 ) * 100`.
        # So the formula produces Percentage.
        # BUT `b3_scraper.py` produces Decimals.
        # If I mix them, the output dataframe will have some rows as decimals (the original ones) and some as percentages (the interpolated ones) unless I convert everything.
        # I MUST be consistent.
        # I will convert the interpolated values back to decimals (divide by 100) to match the scraper's format,
        # UNLESS the user implies they want the whole dataframe transformed.
        # The user provided a formula for the CALCULATION.
        # The formula returns a Percentage.
        # If I simply apply the formula, I get percentages.
        # But I need to fill the gaps in `interpolated_df`.
        # The existing values in `interpolated_df` are Decimals.
        # So I should remove the `* 100` from the end of the calculation to store it as Decimal,
        # OR I should multiply the existing values by 100.
        # Given `b3_scraper` returns decimals, it is safer to keep decimals.
        # So I will calculate using the formula logic but keep the result as decimal.
        # Formula adapted for decimal inputs/outputs:
        # result_decimal = ( ... )^(252/DU) - 1

        # Let's verify this interpretation.
        # User formula: ( ... - 1 ) * 100.
        # If I omit * 100, I get the decimal.
        # Inside: (1 + i_ant/100).
        # If i_ant is percent (10), i_ant/100 is 0.10.
        # My dataframe has 0.10. So I use (1 + df_val).
        # Correct.

        val_ant = i_ant # 0.10
        val_post = i_post # 0.12

        f_ant = (1 + val_ant) ** (du_ant / 252)
        f_post = (1 + val_post) ** (du_post / 252)

        # Calculate for each day in the gap
        for du in range(du_ant + 1, du_post):
             # (( (1 + i_posterior/100)^(DU_posterior/252) ) / ( (1 + i_anterior/100)^(DU_anterior/252) ) )
            ratio = f_post / f_ant

            exponent = (du - du_ant) / (du_post - du_ant)

            # ( ... ) ^ exponent
            term_middle = ratio ** exponent

            # ( f_ant * term_middle )
            term_combined = f_ant * term_middle

            # ( ... ) ^ (252/DU)
            result_plus_one = term_combined ** (252 / du)

            result_decimal = result_plus_one - 1

            interpolated_df.loc[du, 'taxas252'] = result_decimal

    return interpolated_df

def get_b3_curve_interpolated():
    """
    Main function to get the latest interpolated B3 curve.
    """
    df, ref_date = fetch_latest_curve()
    if df is None:
        print("Could not fetch B3 curve data.")
        return None

    print(f"Interpolating curve for {ref_date}...")
    final_df = interpolate_curve(df)

    # Store reference date in the dataframe (optional but useful)
    # The scraping function returns index=Days, col=taxas252.
    # Maybe we want to return the date as well?
    # The user asked: "Armazena este dado em um dataframe que possa ser consultado por um outro código."
    # The user didn't explicitly ask for the date column, but it's crucial context.
    # However, `b3_scraper` returns just rates.
    # I'll add the date as an attribute or column if needed, but for now just the rates as requested.

    return final_df

if __name__ == "__main__":
    df = get_b3_curve_interpolated()
    if df is not None:
        print("Final DataFrame Head:")
        print(df.head())
        print("Final DataFrame Tail:")
        print(df.tail())
