import pandas as pd
import json
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.widgets as widgets
import requests

# Your API Key for Alpha Vantage
ALPHA_VANTAGE_API_KEY = "WPKRZRI7UK096O5E"

class StockAPI:
    def __init__(self, api_key=ALPHA_VANTAGE_API_KEY):
        self.api_key = api_key

    def get_stock_info(self, stock, market):
        symbol = f"{stock}.{market}" if market != "NASDAQ" else stock
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={self.api_key}'

        r = requests.get(url)

        # Try parsing JSON response
        try:
            data = r.json()
        except ValueError:
            raise ValueError("Failed to decode JSON from API response. Response was:\n" + r.text)

        # Check for valid time series data
        if "Time Series (Daily)" not in data:
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")
            elif "Note" in data:
                raise ValueError(f"API Limit Reached: {data['Note']}")
            else:
                raise ValueError(f"Invalid data received from API. Response: {json.dumps(data, indent=2)}")

        return data
    
class StockAnalyzer:
    def __init__(self):
        pass

    def json_to_dataframe(self, json_data, stock_symbol, market):
        if "Time Series (Daily)" not in json_data:
            raise ValueError("Invalid data received from API. Response was:\n" + json.dumps(json_data, indent=2))

        time_series_data = json_data['Time Series (Daily)']
        df_data = []

        for date_str, values in time_series_data.items():
            data_row = {'date': date_str}
            for key, value in values.items():
                new_key = key.split('. ')[1]  # Extract proper field name
                data_row[new_key] = float(value)
            df_data.append(data_row)

        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])

        eastern = pytz.timezone('US/Eastern')
        ist = pytz.timezone('Asia/Kolkata')
        df['date'] = df['date'].dt.tz_localize(eastern).dt.tz_convert(ist)
        df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S')

        df['stock'] = stock_symbol
        df['market'] = market

        df = df.set_index('date')
        df = df.sort_index()  # Ensure it's sorted for rolling operations
        return df

    def plot_stock_data(self, df, stock_symbol, market, image_path):
        # Calculate Moving Averages and Bollinger Bands
        df['MA_7'] = df['close'].rolling(window=7).mean()
        df['MA_20'] = df['close'].rolling(window=20).mean()
        df['BB_upper'] = df['MA_20'] + 2 * df['close'].rolling(window=20).std()
        df['BB_lower'] = df['MA_20'] - 2 * df['close'].rolling(window=20).std()

        plt.figure(figsize=(16, 12))

        # Chart 1: Closing Price + MAs + Bollinger Bands
        plt.subplot(3, 1, 1)
        dates = pd.to_datetime(df.index)
        plt.plot(dates, df['close'], label='Close Price', color='blue', linewidth=1.5)
        plt.plot(dates, df['MA_7'], label='7-Day MA', color='orange')
        plt.plot(dates, df['MA_20'], label='20-Day MA', color='red')
        plt.plot(dates, df['BB_upper'], label='Upper BB', linestyle='--', color='green')
        plt.plot(dates, df['BB_lower'], label='Lower BB', linestyle='--', color='green')
        plt.fill_between(dates, df['BB_lower'], df['BB_upper'], color='green', alpha=0.1)
        plt.title(f'{stock_symbol} Price + Moving Averages + Bollinger Bands ({market})')
        plt.xlabel('Date (IST)')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)

        # Chart 2: Volume
        plt.subplot(3, 1, 2)
        plt.bar(dates, df['volume'], label='Volume', color='gray')
        plt.title('Trading Volume')
        plt.xlabel('Date')
        plt.ylabel('Volume')
        plt.grid(True)

        # Chart 3: 7 vs 20 Moving Average Spread
        plt.subplot(3, 1, 3)
        spread = df['MA_7'] - df['MA_20']
        plt.plot(dates, spread, color='purple', label='7-Day MA - 20-Day MA')
        plt.axhline(0, linestyle='--', color='black')
        plt.title('Momentum Indicator: MA(7) - MA(20)')
        plt.xlabel('Date')
        plt.ylabel('Spread')
        plt.grid(True)
        plt.legend()

        for ax in plt.gcf().axes:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            plt.gcf().autofmt_xdate()

        cursor = widgets.Cursor(plt.gca(), color='red', linewidth=1)

        plt.tight_layout()
        plt.savefig(image_path)
        plt.close()
