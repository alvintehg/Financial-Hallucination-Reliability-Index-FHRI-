# scripts/fetch_finnhub.py
import os, json, time
import finnhub
from pathlib import Path

API_KEY = os.environ.get("FINNHUB_API_KEY")
if not API_KEY:
    raise SystemExit("Set FINNHUB_API_KEY env var before running")

client = finnhub.Client(api_key=API_KEY)
OUTDIR = Path("data/trusted_docs")
OUTDIR.mkdir(parents=True, exist_ok=True)

def save_json(path, obj):
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

def fetch_company_news(ticker, days=7):
    end = int(time.time())
    start = end - days * 24 * 3600
    news = client.company_news(ticker, _from=time.strftime("%Y-%m-%d", time.gmtime(start)),
                               to=time.strftime("%Y-%m-%d", time.gmtime(end)))
    for i, art in enumerate(news):
        pid = f"{ticker}_news_{art.get('datetime', i)}"
        save_json(OUTDIR / f"{pid}.json", {"type":"news","ticker":ticker, **art})
    print(f"Saved {len(news)} news for {ticker}")

def fetch_quote(ticker):
    q = client.quote(ticker)
    save_json(OUTDIR / f"{ticker}_quote_{int(time.time())}.json", {"type":"quote","ticker":ticker,"quote":q})
    print("Saved quote for", ticker)

if __name__ == "__main__":
    tickers = ["AAPL","MSFT","GOOGL"]  # change as needed
    for t in tickers:
        try:
            fetch_company_news(t, days=30)
            fetch_quote(t)
            time.sleep(1)  # respect rate limits
        except Exception as e:
            print("Error", t, e)
