from langchain_core.tools import tool
import yfinance as yf
from datetime import datetime

# Commodity name to ticker symbol mapping
COMMODITY_SYMBOLS = {
    "wheat": "ZW=F",
    "soy": "ZS=F",
    "soybeans": "ZS=F",
    "corn": "ZC=F",
    "sugar": "SB=F",
    "cotton": "CT=F",
    "rice": "ZR=F"
}


@tool
def get_commodity_price(commodity: str) -> str:
    """
    Fetch current commodity price and metrics using yfinance futures data.
    Supports: wheat, soy, corn, sugar, cotton, rice

    Args:
        commodity: Commodity name (wheat, soy, corn, sugar, cotton, rice)

    Returns:
        Formatted string with price, change%, volume, and 52-week high/low
    """
    commodity_lower = commodity.lower().strip()

    # Map commodity name to ticker
    if commodity_lower not in COMMODITY_SYMBOLS:
        valid = ", ".join(COMMODITY_SYMBOLS.keys())
        return f"Unknown commodity '{commodity}'. Valid options: {valid}"

    ticker_symbol = COMMODITY_SYMBOLS[commodity_lower]

    try:
        # Fetch commodity data
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="1d")
        info = ticker.info

        if hist.empty:
            return f"No data available for {commodity.capitalize()} ({ticker_symbol})"

        # Get latest data
        latest = hist.iloc[-1]
        price = latest['Close']
        open_price = latest['Open']
        high = latest['High']
        low = latest['Low']
        volume = latest['Volume']

        # Get previous close for change calculation
        hist_5d = ticker.history(period="5d")
        if len(hist_5d) >= 2:
            prev_close = hist_5d.iloc[-2]['Close']
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        else:
            prev_close = price
            change = 0
            change_pct = 0

        # Get 52-week data
        hist_1y = ticker.history(period="1y")
        if not hist_1y.empty:
            week_52_high = hist_1y['High'].max()
            week_52_low = hist_1y['Low'].min()
        else:
            week_52_high = high
            week_52_low = low

        # Determine direction
        direction = "[UP]" if change >= 0 else "[DOWN]"

        # Format current date
        today = datetime.now().strftime("%Y-%m-%d")

        # Format volume
        volume_str = f"{int(volume):,}" if volume > 0 else "N/A"

        return f"""
Commodity: {commodity.upper()} ({ticker_symbol})

Price: ${price:.2f}  {direction} ${change:+.2f} ({change_pct:+.2f}%)
As of: {today}

Today's Trading:
  Open:  ${open_price:.2f}
  High:  ${high:.2f}
  Low:   ${low:.2f}
  Prev Close: ${prev_close:.2f}
  Volume: {volume_str}

52-Week Range:
  High: ${week_52_high:.2f}
  Low:  ${week_52_low:.2f}
""".strip()

    except Exception as e:
        return f"Error fetching {commodity} price: {str(e)}"
