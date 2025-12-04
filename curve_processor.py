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

    return final_df

if __name__ == "__main__":
    df = get_b3_curve_interpolated()
    if df is not None:
        print("Final DataFrame Head:")
        print(df.head())
        print("Final DataFrame Tail:")
        print(df.tail())
