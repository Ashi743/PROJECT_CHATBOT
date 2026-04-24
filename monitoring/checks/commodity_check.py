import yfinance as yf
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

COMMODITY_SYMBOLS = {
    "wheat": "ZW=F",
    "soy": "ZS=F",
    "corn": "ZC=F",
    "sugar": "SB=F"
}


def check_commodities() -> dict:
    results = {}

    for commodity, symbol in COMMODITY_SYMBOLS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")

            if hist.empty:
                results[commodity] = {
                    "price": None,
                    "change": None,
                    "status": "[DOWN]",
                    "volume": None,
                    "updated": datetime.now().strftime("%d %b %Y %H:%M")
                }
                continue

            latest = hist.iloc[-1]
            price = float(latest['Close'])
            volume = int(latest['Volume'])

            if len(hist) >= 2:
                prev_close = float(hist.iloc[-2]['Close'])
                change = ((price - prev_close) / prev_close * 100) if prev_close != 0 else 0
            else:
                change = 0

            if change < -1.5:
                status = "[ALERT]"
            elif change > 1.5:
                status = "[SURGE]"
            else:
                status = "[OK]"

            results[commodity] = {
                "price": round(price, 2),
                "change": round(change, 2),
                "status": status,
                "volume": volume,
                "updated": datetime.now().strftime("%d %b %Y %H:%M")
            }

        except Exception as e:
            logger.error(f"Error checking {commodity}: {e}")
            results[commodity] = {
                "price": None,
                "change": None,
                "status": "[ERROR]",
                "volume": None,
                "updated": datetime.now().strftime("%d %b %Y %H:%M"),
                "error": str(e)
            }

    return results


if __name__ == "__main__":
    import json
    result = check_commodities()
    print(json.dumps(result, indent=2))
