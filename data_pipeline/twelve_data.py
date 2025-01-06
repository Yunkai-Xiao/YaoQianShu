import os
import requests
import pandas as pd

class TwelveDataClient:
    def __init__(self):
        print(os.getenv("TWELVE_DATA_API_KEY"))
        self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        self.base_url = 'https://api.twelvedata.com/'

    def _request(self, endpoint, params):
        url = f"{self.base_url}{endpoint}"
        params['apikey'] = self.api_key
        response = requests.get(url, params=params)
        data = response.json()
        if 'status' in data and data['status'] == 'error':
            raise Exception(f"Error: {data['message']}")
        return data

    def get_time_series(self, symbol, interval='1min', outputsize=30, **kwargs):
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
        }
        params.update(kwargs)
        data = self._request('time_series', params)
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df

    def get_quote(self, symbol):
        params = {'symbol': symbol}
        data = self._request('quote', params)
        return data

    def get_technical_indicator(self, symbol, interval, indicator, **kwargs):
        params = {
            'symbol': symbol,
            'interval': interval,
            'indicator': indicator,
        }
        params.update(kwargs)
        data = self._request('technical_indicator', params)
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        return df
