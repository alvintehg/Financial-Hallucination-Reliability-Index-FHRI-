# Live Portfolio Integration - Setup Guide

## Overview

Your portfolio is now connected to live market data! The system fetches real-time prices from Finnhub (with TwelveData and yfinance as fallbacks) and calculates your portfolio value, P&L, and allocations automatically.

## Quick Start

### 1. Configure Your Holdings

Edit the `portfolio.json` file in the project root to match your actual Moomoo holdings:

```json
{
  "holdings": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "shares": 50,
      "cost_basis": 150.00,
      "asset_type": "equity"
    }
  ]
}
```

**Fields:**
- `symbol`: Stock ticker (e.g., "AAPL", "TSLA")
- `name`: Display name
- `shares`: Number of shares you own
- `cost_basis`: Your average purchase price per share
- `asset_type`: Either "equity" (stocks/ETFs) or "crypto" (BTC, ETH, etc.)

### 2. Start the Backend

```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python -m uvicorn src.server:app --port 8000 --reload
```

### 3. Start the Frontend

```bash
cd frontend
npm start
```

### 4. View Your Live Portfolio

Navigate to the Dashboard - your portfolio will automatically:
- Fetch live prices every 30 seconds
- Calculate daily P&L
- Show total unrealized gains/losses
- Display allocation percentages
- Indicate which data source was used (Finnhub, TwelveData, or yfinance)

## Features

### Live Data
- **Auto-refresh**: Updates every 30 seconds
- **Manual refresh**: Click the refresh button anytime
- **Multi-source fallback**: Automatically tries Finnhub → TwelveData → yfinance
- **45-second cache**: Prevents API rate limiting

### Calculations
- **Market Value**: Current price × shares
- **Unrealized P&L**: (Current price - cost basis) × shares
- **Allocation %**: Holding value / total portfolio value × 100
- **Daily Change**: Today's price movement impact on your holdings

### API Endpoints

All portfolio endpoints are available at `http://127.0.0.1:8000`:

#### GET /portfolio/live
Fetch live portfolio with real-time prices and calculations.

**Response:**
```json
{
  "summary": {
    "total_value": 50000.00,
    "total_pnl": 5000.00,
    "total_pnl_pct": 11.11,
    "daily_change": 250.00,
    "daily_change_pct": 0.50,
    "positions_count": 5
  },
  "holdings": [...]
}
```

#### POST /portfolio/holdings/add
Add a new holding.

**Request:**
```json
{
  "symbol": "AAPL",
  "shares": 50,
  "cost_basis": 150.00,
  "name": "Apple Inc.",
  "asset_type": "equity"
}
```

#### POST /portfolio/holdings/update
Update shares or cost basis for an existing holding.

**Request:**
```json
{
  "symbol": "AAPL",
  "shares": 60,
  "cost_basis": 155.00
}
```

#### POST /portfolio/holdings/remove
Remove a holding from your portfolio.

**Request:**
```json
{
  "symbol": "AAPL"
}
```

#### GET /portfolio/holdings
Get raw holdings configuration (without live prices).

## How to Sync with Moomoo

### Option 1: Manual Entry (Current Implementation)
1. Open your Moomoo app/website
2. View your holdings
3. For each position, copy the:
   - Ticker symbol
   - Number of shares
   - Average cost (your purchase price)
4. Add to `portfolio.json`

### Option 2: Export from Moomoo (Recommended)
1. In Moomoo, export your portfolio to CSV
2. Create a simple script to convert CSV to `portfolio.json` format
3. Run the script whenever you want to sync

### Option 3: Moomoo API Integration (Future)
For automatic syncing, you would need to:
1. Sign up for Moomoo OpenAPI access
2. Get API credentials
3. Implement OAuth authentication
4. Add automatic sync functionality

## Supported Assets

### Stocks/ETFs
All US-listed stocks and ETFs are supported via Finnhub, TwelveData, and yfinance.

Examples: AAPL, TSLA, SPY, QQQ, VTI, etc.

### Cryptocurrencies
Supported via CoinGecko (free, no API key required):
- BTC (Bitcoin)
- ETH (Ethereum)
- USDT (Tether)
- BNB (Binance Coin)
- SOL (Solana)
- XRP (Ripple)
- ADA (Cardano)
- DOGE (Dogecoin)
- And more...

To add crypto, set `"asset_type": "crypto"` in your holdings.

## Troubleshooting

### "Failed to load portfolio"
- Check that the backend is running on port 8000
- Verify `portfolio.json` exists and is valid JSON
- Check backend logs for errors

### "No price data for symbol"
- Verify the ticker symbol is correct
- Check if the market is open (stocks only update during market hours)
- Try a different symbol to test connectivity

### Incorrect P&L calculations
- Verify your `cost_basis` matches your actual average purchase price
- Ensure `shares` count is accurate
- Remember: P&L is unrealized (paper gains/losses)

### API rate limits
- The system caches prices for 45 seconds
- If you hit rate limits, consider upgrading API keys
- yfinance fallback is unlimited but may be slower

## Next Steps

### Short Term
1. Export your Moomoo portfolio
2. Update `portfolio.json` with your actual holdings
3. Start tracking your live portfolio!

### Medium Term
1. Create a CSV import tool
2. Add portfolio rebalancing suggestions
3. Implement tax-loss harvesting alerts

### Long Term
1. Full Moomoo API integration
2. Automated trade execution
3. Advanced portfolio analytics

## Example Portfolio Configuration

Here's a sample diversified portfolio:

```json
{
  "holdings": [
    {
      "symbol": "SPY",
      "name": "SPDR S&P 500 ETF",
      "shares": 100,
      "cost_basis": 420.00,
      "asset_type": "equity"
    },
    {
      "symbol": "QQQ",
      "name": "Invesco QQQ Trust",
      "shares": 50,
      "cost_basis": 350.00,
      "asset_type": "equity"
    },
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "shares": 0.5,
      "cost_basis": 45000.00,
      "asset_type": "crypto"
    },
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "shares": 75,
      "cost_basis": 175.00,
      "asset_type": "equity"
    },
    {
      "symbol": "TSLA",
      "name": "Tesla Inc.",
      "shares": 25,
      "cost_basis": 240.00,
      "asset_type": "equity"
    }
  ],
  "last_updated": "2025-01-05T00:00:00Z"
}
```

## Need Help?

Check the backend logs for detailed error messages:
```bash
# Backend will show logs like:
# INFO - Fetching live portfolio data...
# INFO - Finnhub: Fetched AAPL @ $180.50 (+2.30%)
# INFO - Portfolio fetched: 5 positions, total value: $50,000.00
```

Enjoy your live portfolio tracking! 🚀
