import yfinance as yf
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

PERIOD_OPTIONS = {
    '1d': '1 Day', '5d': '5 Days', '1mo': '1 Month', '3mo': '3 Months',
    '6mo': '6 Months', '1y': '1 Year', 'ytd': 'Year To Date', 'max': 'Max'
}

class StockDataManager:
    def __init__(self):
        self.stock_cache = {}
        self.executor = ThreadPoolExecutor(max_workers=4)

    def fetch_stock_data(self, symbol, period):
        try:
            if period == '1d':
                end = datetime.now()
                start = end - pd.Timedelta(days=1)
                df = yf.download(symbol, start=start, end=end, interval='1m')
            else:
                df = yf.download(symbol, period=period)

            if df.empty:
                raise ValueError("No data available.")

            df = df.reset_index()
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            elif 'Date' not in df.columns:
                raise ValueError("Unexpected data format.")

            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception as e:
            raise ValueError(f'Failed to fetch data: {str(e)}')

    def get_stock_info(self, symbol):
        if symbol in self.stock_cache:
            return self.stock_cache[symbol]
        stock = yf.Ticker(symbol)
        info = stock.info
        self.stock_cache[symbol] = info
        return info

    def get_current_price(self, symbol):
        try:
            return yf.Ticker(symbol).history(period='1d')['Close'].iloc[-1]
        except:
            return None