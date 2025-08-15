import os
import httpx
from dotenv import load_dotenv

load_dotenv()

STOCK_API_KEY = os.getenv("STOCK_API_KEY")

async def get_stock_info(symbol: str):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval": "5min",  # You can also use 1min, 15min, etc.
        "outputsize": "compact",
        "datatype": "json",
        "apikey": STOCK_API_KEY
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        data = res.json()

        time_series_key = "Time Series (5min)"
        if time_series_key not in data:
            return {"response": f"Error: {data.get('Error Message', 'Could not fetch intraday data.')}"}

        latest_timestamp = sorted(data[time_series_key].keys())[-1]
        latest_data = data[time_series_key][latest_timestamp]

        return {
            "symbol": symbol,
            "timestamp": latest_timestamp,
            "open": latest_data["1. open"],
            "high": latest_data["2. high"],
            "low": latest_data["3. low"],
            "close": latest_data["4. close"],
            "volume": latest_data["5. volume"]
        }
