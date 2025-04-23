import pandas as pd
import yfinance as yf
from tabulate import tabulate

# Load the list of Nifty 500 stocks from the CSV file
file_path = "data/nifty_500list.csv"  # Adjusted to use 'data' folder
stock_nifty = pd.read_csv(file_path)
stocks = [f"{symbol}.NS" for symbol in stock_nifty['Symbol'].head(500).tolist()]


def get_bollinger_bands(symbol):
    data = yf.download(symbol, period='1y', interval='1d')
    if data.empty:
        return {
            'Symbol': symbol,
            'Latest Close': None,
            'Upper Band 2': None,
            'Upper Band 3': None,
            'Is Between 2nd and 3rd': None,
            'Error': 'No data found'
        }

    data['MA200'] = data['Close'].rolling(window=200).mean()
    data['STD'] = data['Close'].rolling(window=200).std()

    # Ensure we have enough data points for calculations
    if pd.isna(data['MA200'].iloc[-1]) or pd.isna(data['STD'].iloc[-1]):
        return {
            'Symbol': symbol,
            'Latest Close': None,
            'Upper Band 2': None,
            'Upper Band 3': None,
            'Is Between 2nd and 3rd': None,
            'Error': 'Not enough data'
        }

    upper_band_2 = float(data['MA200'].iloc[-1] + (data['STD'].iloc[-1] * 2))
    upper_band_3 = float(data['MA200'].iloc[-1] + (data['STD'].iloc[-1] * 3))
    latest_close = float(data['Close'].iloc[-1])

    # Check for NaN values before performing comparison
    if pd.isna(upper_band_2) or pd.isna(upper_band_3) or pd.isna(latest_close):
        return {
            'Symbol': symbol,
            'Latest Close': latest_close,
            'Upper Band 2': upper_band_2,
            'Upper Band 3': upper_band_3,
            'Is Between 2nd and 3rd': None,
            'Error': 'Insufficient data for bands'
        }

    is_between = upper_band_2 < latest_close < upper_band_3
    return {
        'Symbol': symbol,
        'Latest Close': latest_close,
        'Upper Band 2': upper_band_2,
        'Upper Band 3': upper_band_3,
        'Is Between 2nd and 3rd': is_between,
        'Error': None
    }


# Process each stock and get the Bollinger Bands
results = [get_bollinger_bands(stock) for stock in stocks]
results_df = pd.DataFrame(results)
qualifying_stocks_df = results_df[results_df['Is Between 2nd and 3rd'] == True]

# Print the results in a tabular format
print(tabulate(qualifying_stocks_df, headers='keys', tablefmt='psql'))
