from langchain_core.tools import tool
import yfinance as yf
from datetime import datetime
import logging
from utils.rate_limit import rate_limit

logger = logging.getLogger(__name__)

@tool
def get_stock_price(symbol: str) -> str:
    """
    Fetch the current stock price and key metrics for a given stock symbol.
    Use when user asks about stock price, market cap, or stock performance.
    Input must be a valid stock ticker symbol like 'AAPL', 'TSLA', 'GOOGL', 'RELIANCE.BO'.
    """
    rate_limit("stock", 1.0)
    try:
        symbol = symbol.upper()

        # Fetch stock data using yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        info = ticker.info

        if hist.empty:
            return f"No data found for symbol '{symbol}'. Check if the ticker is correct."

        # Get latest data
        latest = hist.iloc[-1]
        price = latest['Close']
        open_price = latest['Open']
        high = latest['High']
        low = latest['Low']
        volume = latest['Volume']

        # Get previous close
        hist_2d = ticker.history(period="2d")
        if len(hist_2d) >= 2:
            prev_close = hist_2d.iloc[-2]['Close']
            change = price - prev_close
            change_pct = (change / prev_close * 100) if prev_close != 0 else 0
        else:
            prev_close = price
            change = 0
            change_pct = 0

        # Get company info
        company_name = info.get("longName", symbol)
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")
        market_cap = info.get("marketCap", "N/A")
        pe_ratio = info.get("trailingPE", "N/A")
        week_52_high = info.get("fiftyTwoWeekHigh", "N/A")
        week_52_low = info.get("fiftyTwoWeekLow", "N/A")
        dividend_yield = info.get("dividendYield", "N/A")

        # Format market cap
        if isinstance(market_cap, (int, float)) and market_cap != "N/A":
            mc = float(market_cap)
            if mc >= 1_000_000_000_000:
                market_cap = f"${mc / 1_000_000_000_000:.2f}T"
            elif mc >= 1_000_000_000:
                market_cap = f"${mc / 1_000_000_000:.2f}B"
            elif mc >= 1_000_000:
                market_cap = f"${mc / 1_000_000:.2f}M"

        # Format PE ratio
        if isinstance(pe_ratio, (int, float)) and pe_ratio != "N/A":
            pe_ratio = f"{pe_ratio:.2f}"

        # Format dividend yield
        if isinstance(dividend_yield, (int, float)) and dividend_yield != "N/A":
            dividend_yield = f"{dividend_yield*100:.2f}%"

        # Determine direction
        try:
            direction = "[UP]" if change >= 0 else "[DOWN]"
        except Exception as e:
            logger.warning(f"Could not determine price direction: {e}")
            direction = ""

        # Format current date
        today = datetime.now().strftime("%Y-%m-%d")

        return f"""
Stock: {company_name} ({symbol})
Sector: {sector} | Industry: {industry}

Price: ${price:.2f}  {direction} ${change:+.2f} ({change_pct:+.2f}%)
As of: {today}

Today:
  Open:  ${open_price:.2f}
  High:  ${high:.2f}
  Low:   ${low:.2f}
  Prev Close: ${prev_close:.2f}
  Volume: {int(volume):,}

Fundamentals:
  Market Cap:     {market_cap}
  P/E Ratio:      {pe_ratio}
  52-Week High:   ${week_52_high}
  52-Week Low:    ${week_52_low}
  Dividend Yield: {dividend_yield}
""".strip()

    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch stock price for {symbol}: {e}")
        return f"[ERROR] Could not fetch stock data for {symbol}. Please check the ticker symbol."
