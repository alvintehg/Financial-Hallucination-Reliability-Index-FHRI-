# Cryptocurrency Support

## ✅ Now Supported!

Your chatbot now supports **real-time cryptocurrency data** in addition to stocks!

---

## 🪙 Supported Cryptocurrencies

| Crypto | Symbols | Example Query |
|--------|---------|---------------|
| Bitcoin | BTC, BITCOIN | "What is Bitcoin price?" or "How is BTC doing?" |
| Ethereum | ETH, ETHEREUM | "What is ETH price?" |
| Binance Coin | BNB, BINANCE | "Show me BNB price" |
| Ripple | XRP, RIPPLE | "What is XRP trading at?" |
| Cardano | ADA, CARDANO | "How is ADA performing?" |
| Dogecoin | DOGE, DOGECOIN | "What's DOGE price?" |
| Solana | SOL, SOLANA | "Tell me SOL price" |
| Polkadot | DOT, POLKADOT | "What is DOT worth?" |
| Polygon | MATIC, POLYGON | "Show me MATIC price" |
| Chainlink | LINK, CHAINLINK | "What is LINK price?" |
| Avalanche | AVAX, AVALANCHE | "How is AVAX doing?" |
| Uniswap | UNI, UNISWAP | "What is UNI trading at?" |

---

## 📊 What Data You Get

### 1. Real-Time Price (24/7)
- Current price in USD
- 24-hour high/low
- 24-hour price change ($ and %)
- Exchange source (Binance)

### 2. Latest Crypto News
- Top 3 recent articles
- Headlines from CoinDesk, Cointelegraph, etc.
- Timestamps

### 3. Market Context
- Real-time (crypto markets never close!)
- No stale data warnings

---

## 🎯 Example Queries

### Single Cryptocurrency
```
✅ "What is Bitcoin price right now?"
✅ "How is BTC doing?"
✅ "Tell me ETH price"
✅ "What's the latest crypto news?"
```

### Compare Multiple Cryptos
```
✅ "Compare BTC and ETH prices"
✅ "Which is more expensive, Bitcoin or Ethereum?"
✅ "Show me prices for BTC, ETH, and ADA"
```

### Price Changes
```
✅ "How much did Bitcoin change in 24 hours?"
✅ "Is ETH up or down today?"
✅ "What's BTC's 24h high?"
```

### News Queries
```
✅ "What's the latest Bitcoin news?"
✅ "Any recent crypto news?"
✅ "Tell me about cryptocurrency market"
```

### Mixed Stocks + Crypto
```
✅ "Compare COIN stock and Bitcoin price"
✅ "Show me AAPL and BTC prices"
```

---

## 📝 How to Ask

### ✅ CORRECT Ways

**Use crypto symbols or names:**
```
"What is BTC price?"
"What is Bitcoin price?"
"How is ETH doing?"
"Tell me Ethereum price"
```

**Include crypto keywords:**
- crypto / cryptocurrency
- coin
- token
- blockchain

Example:
```
"What is the price of BTC cryptocurrency?"
"How is crypto market doing?"
```

### ❌ WRONG Ways

```
❌ "What is bitcoin price?" (lowercase - might not be detected)
❌ "How much is crypto?" (too vague, no specific coin)
```

**Tip:** Always use UPPERCASE for crypto symbols (BTC, ETH, etc.)

---

## 🆚 Stocks vs Crypto

| Feature | Stocks (COIN, AAPL) | Crypto (BTC, ETH) |
|---------|---------------------|-------------------|
| Trading Hours | Mon-Fri 9:30 AM - 4:00 PM ET | 24/7/365 |
| Data Freshness | Live during market hours | Always live |
| Stale Data Warning | Yes (when market closed) | No (always fresh) |
| Example Symbol | AAPL, MSFT, COIN | BTC, ETH, DOGE |
| Price Range | $1-$1000s | $0.0001-$100,000+ |
| News Sources | Financial news | Crypto-specific news |

---

## 🧪 Test Questions

### Basic Crypto Queries
```
1. "What is Bitcoin price right now?"
   Expected: Real-time BTC price from Binance

2. "How is ETH doing?"
   Expected: Ethereum price + 24h change

3. "What's the latest crypto news?"
   Expected: Top 3 recent crypto news articles
```

### Advanced
```
4. "Compare Bitcoin and Ethereum prices"
   Expected: Both BTC and ETH data

5. "Show me BTC price and recent news"
   Expected: Price + news integration

6. "What's BTC 24-hour change?"
   Expected: Price change in $ and %
```

### Mixed Queries
```
7. "Compare COIN stock and Bitcoin price"
   Expected: COIN stock data + BTC crypto data

8. "Show me AAPL and BTC"
   Expected: Apple stock + Bitcoin crypto
```

---

## 🔍 How It Works

### Symbol Detection
```python
Query: "What is Bitcoin price?"
→ Detects: "BITCOIN"
→ Normalizes to: "BINANCE:BTCUSDT"
→ Fetches from Finnhub API
→ Returns real-time price
```

### Data Structure
```
BTC Cryptocurrency Quote (as of 2025-11-01 23:30:24 UTC):
Current Price: $110,119.99
24h High: $110,632.07 | 24h Low: $108,635
24h Change: $-322.83 (-0.29%)
Exchange: BINANCE

Latest Cryptocurrency News:
- [2025-11-01 22:00] Satoshi's Bitcoin Whitepaper Turns 17...
- [2025-11-01 21:30] Crypto's changing demographics...
```

---

## ⚙️ Configuration

### Enable/Disable Crypto

**Via API Request:**
```json
{
  "text": "What is Bitcoin price?",
  "use_crypto": true,  // Enable crypto (default: true)
  "use_realtime": true // Enable stock data (default: true)
}
```

**Disable Crypto:**
```json
{
  "text": "What is Bitcoin price?",
  "use_crypto": false  // Crypto disabled, only static data
}
```

---

## 🚀 Quick Start

### 1. Restart the server
```bash
uvicorn src.server:app --port 8000
```

### 2. Ask a crypto question
```
"What is Bitcoin price right now?"
```

### 3. Expected response
```
Based on the most recent data from Binance, Bitcoin (BTC) is currently
trading at $110,119.99. The price has decreased by $322.83 (-0.29%)
over the last 24 hours, with a 24-hour high of $110,632.07 and a low
of $108,635.00.

Recent crypto news:
- Satoshi's Bitcoin Whitepaper Turns 17: From Cypherpunk Rebellion
  to Wall Street Staple (CoinDesk, Nov 1)
```

---

## 📊 Response Metadata

The response now includes crypto metadata:

```json
{
  "answer": "Bitcoin is trading at $110,119.99...",
  "meta": {
    "crypto_data_used": true,
    "crypto_symbols": ["BTC"],
    "detectors_used": {
      "realtime_crypto": true,
      "realtime_stocks": false
    }
  }
}
```

---

## 🔧 Troubleshooting

### "No crypto data found"

**Cause:** Symbol not detected

**Solution:**
- Use uppercase: "BTC" not "btc"
- Use symbol or full name: "BTC" or "Bitcoin"
- Add crypto keyword: "What is BTC cryptocurrency price?"

### "Crypto news not showing"

**Expected Behavior:**
- News is general crypto news, not coin-specific
- Shows top 3 recent articles from crypto news sources

### "Price seems wrong"

**Check:**
- Crypto markets are 24/7, prices constantly change
- Price is from Binance exchange
- Timestamp shows exact quote time

---

## 🎓 Important Notes

### 1. Crypto vs Stock Ticker Confusion

**COIN** = Coinbase stock (company)
**BTC** = Bitcoin cryptocurrency

```
"What is COIN price?"  → Coinbase STOCK price
"What is BTC price?"   → Bitcoin CRYPTO price
```

### 2. Data Source

All crypto data comes from **Finnhub API** using **Binance** exchange prices

### 3. Real-Time vs Historical

- Crypto prices: Always real-time (24/7 trading)
- Stock prices: Real-time during market hours, last close otherwise

### 4. FHRI Scoring

Crypto queries get FHRI scores just like stock queries:
- High grounding (real-time data cited)
- High numerical accuracy (exact prices)
- High temporal consistency (timestamps)

---

## 📖 Example Session

```
User: "What is Bitcoin price?"