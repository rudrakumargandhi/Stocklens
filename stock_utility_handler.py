import pandas as pd
import json
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.widgets as widgets
import requests
from matplotlib.widgets import Cursor

# Your API Key for Alpha Vantage
ALPHA_VANTAGE_API_KEY = "5BPONE0YQY8ZH17G"

class StockAPI:
    def __init__(self, api_key=ALPHA_VANTAGE_API_KEY):
        self.api_key = api_key

    
    def get_fundamental_data(self, symbol):
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Failed to fetch fundamental data.")
    

    def get_live_price(self, stock, market="BSE"):
        import requests

        if market == "BSE":
            symbol = f"BOM:{stock}"
        elif market == "NASDAQ":
            symbol = stock  # no prefix needed for NASDAQ
        else:
            raise ValueError("Unsupported market")

        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()

        try:
            return float(data["Global Quote"]["05. price"])
        except (KeyError, ValueError):
            raise ValueError("Could not fetch price")
    

    def get_stock_data(self, stock, market):
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
    
    def compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
    
    def compute_macd(self, series, short=12, long=26, signal=9):
        ema_short = series.ewm(span=short, adjust=False).mean()
        ema_long = series.ewm(span=long, adjust=False).mean()
        macd_line = ema_short - ema_long
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram


    def plot_stock_data(self, df, stock_symbol, market, image_path):
    # Calculate Moving Averages and Bollinger Bands
        df['MA_7'] = df['close'].rolling(window=7).mean()
        df['MA_20'] = df['close'].rolling(window=20).mean()
        df['BB_upper'] = df['MA_20'] + 2 * df['close'].rolling(window=20).std()
        df['BB_lower'] = df['MA_20'] - 2 * df['close'].rolling(window=20).std()

        dates = pd.to_datetime(df.index)

        fig, axs = plt.subplots(5, 1, figsize=(16, 16), sharex=True)

    # Chart 1: Closing Price + MAs + Bollinger Bands
        axs[0].plot(dates, df['close'], label='Close Price', color='blue', linewidth=1.5)
        axs[0].plot(dates, df['MA_7'], label='7-Day MA', color='orange')
        axs[0].plot(dates, df['MA_20'], label='20-Day MA', color='red')
        axs[0].plot(dates, df['BB_upper'], label='Upper BB', linestyle='--', color='green')
        axs[0].plot(dates, df['BB_lower'], label='Lower BB', linestyle='--', color='green')
        axs[0].fill_between(dates, df['BB_lower'], df['BB_upper'], color='green', alpha=0.1)
        axs[0].set_title(f'{stock_symbol} Price + Moving Averages + Bollinger Bands ({market})')
        axs[0].set_ylabel('Price')
        axs[0].legend()
        axs[0].grid(True)

    # Chart 2: Volume
        axs[1].bar(dates, df['volume'], label='Volume', color='gray')
        axs[1].set_title('Trading Volume')
        axs[1].set_ylabel('Volume')
        axs[1].grid(True)

    # Chart 3: 7 vs 20 Moving Average Spread
        spread = df['MA_7'] - df['MA_20']
        axs[2].plot(dates, spread, color='purple', label='7-Day MA - 20-Day MA')
        axs[2].axhline(0, linestyle='--', color='black')
        axs[2].set_title('Momentum Indicator: MA(7) - MA(20)')
        axs[2].set_xlabel('Date')
        axs[2].set_ylabel('Spread')
        axs[2].legend()
        axs[2].grid(True)
    # Chart 4: RSI
        df['RSI'] = self.compute_rsi(df['close'])
        axs[3].plot(dates, df['RSI'], label='RSI', color='teal')
        axs[3].axhline(70, color='red', linestyle='--', label='Overbought (70)')
        axs[3].axhline(30, color='green', linestyle='--', label='Oversold (30)')
        axs[3].set_title('Relative Strength Index (RSI)')
        axs[3].set_ylabel('RSI')
        axs[3].legend()
        axs[3].grid(True)

    # Chart 5: MACD
        df['MACD'], df['Signal'], df['MACD_Hist'] = self.compute_macd(df['close'])
        axs[4].plot(dates, df['MACD'], label='MACD Line', color='blue')
        axs[4].plot(dates, df['Signal'], label='Signal Line', color='orange')
        axs[4].bar(dates, df['MACD_Hist'], label='Histogram', color='grey', alpha=0.5)
        axs[4].set_title('MACD (12-26-9)')
        axs[4].set_ylabel('MACD')
        axs[4].legend()
        axs[4].grid(True)    

    # Date formatting for all axes
        for ax in axs:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

        fig.autofmt_xdate()

    # Optional: Cursor only for final subplot
        Cursor(axs[-1], color='red', linewidth=1)

        plt.tight_layout()
        fig.savefig(image_path)
        return fig  # Return for use with st.pyplot(fig)
