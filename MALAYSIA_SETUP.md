# Portfolio Setup for Moomoo Malaysia

## Overview

Since **Moomoo Malaysia doesn't support OpenD API** (only available for FUTU HK, Moomoo US, SG, and AU), we've created a **manual entry system** that still provides live portfolio tracking with real-time prices.

## How It Works

1. **You manually enter your holdings** (one-time setup)
2. **System fetches live prices** automatically from Finnhub/TwelveData/yfinance
3. **Dashboard updates every 30 seconds** with real-time P&L calculations
4. **You can edit holdings anytime** when your portfolio changes

## Step-by-Step Setup

### Step 1: Start Your Application

Make sure both backend and frontend are running:

**Backend:**
```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
python -m uvicorn src.server:app --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm start
```

### Step 2: Access Holdings Manager

1. Open your dashboard: http://localhost:3000/dashboard
2. Click on **"Manage Holdings"** in the sidebar (icon with pencil/edit)
3. You'll see a table showing your current holdings

### Step 3: Clear Sample Data

The system comes with sample holdings (SPY, QQQ, AGG, VXUS, VNQ). You need to remove these first:

1. Click the **red delete icon** next to each sample holding
2. Confirm deletion
3. Repeat until the table is empty

### Step 4: Add Your Real Moomoo Holdings

For each stock/ETF you own in Moomoo:

1. Click **"Add Holding"** button
2. Fill in the form:
   - **Stock Symbol**: Ticker symbol (e.g., `AAPL`, `TSLA`, `SPY`)
   - **Company Name**: Optional, will use symbol if not provided
   - **Number of Shares**: Total shares you own (e.g., `100`)
   - **Cost Basis**: Your average purchase price per share (e.g., `150.00`)
3. Click **"Add"**

**Example:**
- Symbol: `AAPL`
- Name: `Apple Inc.`
- Shares: `50`
- Cost Basis: `150.00`

### Step 5: View Live Portfolio

1. Go back to **"Dashboard"** or **"Portfolio"** tab
2. Your portfolio will now show:
   - ✅ **Real positions** you entered
   - ✅ **Live market prices** (auto-updated every 30 seconds)
   - ✅ **Calculated P&L** (Market Value - Total Cost)
   - ✅ **Daily changes** and percentage gains/losses
   - ✅ **Allocation percentages**

## Managing Your Holdings

### Edit a Holding

When you buy/sell shares or need to update cost basis:

1. Go to **"Manage Holdings"**
2. Click the **blue edit icon** next to the holding
3. Update shares or cost basis
4. Click **"Update"**

### Remove a Holding

When you sell all shares:

1. Go to **"Manage Holdings"**
2. Click the **red delete icon**
3. Confirm deletion

### Add New Holdings

When you buy new stocks:

1. Go to **"Manage Holdings"**
2. Click **"Add Holding"**
3. Enter the details
4. Click **"Add"**

## Finding Your Holdings Info in Moomoo

To get the information you need to enter:

1. Open **Moomoo app** (desktop or mobile)
2. Go to **"Portfolio"** or **"Positions"** tab
3. For each stock, note:
   - **Symbol**: Shown next to stock name
   - **Quantity**: Number of shares you own
   - **Avg Cost**: Your average purchase price per share
   - **Current Price**: This will be fetched automatically, no need to enter

## Example: Complete Setup

Let's say your Moomoo portfolio has:
- 50 shares of AAPL bought at $150.00
- 100 shares of TSLA bought at $200.00
- 75 shares of NVDA bought at $450.00

### Steps:

1. **Remove sample holdings** (SPY, QQQ, AGG, VXUS, VNQ)

2. **Add AAPL:**
   - Symbol: `AAPL`
   - Shares: `50`
   - Cost Basis: `150.00`

3. **Add TSLA:**
   - Symbol: `TSLA`
   - Shares: `100`
   - Cost Basis: `200.00`

4. **Add NVDA:**
   - Symbol: `NVDA`
   - Shares: `75`
   - Cost Basis: `450.00`

5. **Go to Dashboard** - You'll see your real portfolio with live prices!

## Live Data Features

Your dashboard will automatically show:

### Portfolio Overview
- **Total Portfolio Value**: Sum of all positions at current prices
- **Daily Change**: Today's gain/loss in $ and %
- **Total P&L**: Unrealized profit/loss since purchase
- **Active Positions**: Number of holdings

### Top Holdings
- Each stock with current market value
- Real-time price changes
- P&L per position
- Allocation percentage

### Market Overview
- Major indices (S&P 500, Dow, Nasdaq, Russell 2000)
- Top movers (NVDA, TSLA, AAPL, META, GOOGL, AMZN)
- Real-time updates

## Tips

1. **Keep Cost Basis Updated**: When you buy more shares at different prices, calculate your new average cost:
   ```
   New Avg Cost = (Old Shares × Old Cost + New Shares × New Cost) / Total Shares
   ```

2. **Use Correct Symbols**: Make sure to use the exact ticker symbol from Moomoo (usually US symbols like AAPL, not local codes)

3. **Partial Sales**: If you sell some shares:
   - Edit the holding
   - Update to new share count
   - Keep the same cost basis (your original average)

4. **Manual Refresh**: Click the refresh icon on Portfolio Overview to force an immediate price update

5. **Check Holdings List**: Regularly review "Manage Holdings" to ensure it matches your actual Moomoo portfolio

## Data Sources

The system fetches live prices from:
1. **Finnhub** (primary)
2. **TwelveData** (fallback)
3. **yfinance** (backup)

All prices are cached for 45 seconds to prevent API rate limits.

## Limitations

Since Moomoo Malaysia doesn't support API:
- ❌ **No automatic sync** from Moomoo
- ❌ **No real-time order execution**
- ❌ **Manual updates required** when you trade

However, you still get:
- ✅ **Live prices** for all your holdings
- ✅ **Real-time P&L calculations**
- ✅ **Portfolio analytics**
- ✅ **AI financial advisor** based on your real portfolio

## Alternative: CSV Import (Future Enhancement)

If Moomoo allows exporting your portfolio to CSV:
1. Export from Moomoo
2. We can add a CSV import feature
3. One-click portfolio sync

Contact support if you'd like this feature added!

## Troubleshooting

### Holdings not showing in dashboard
- Go to "Manage Holdings" and verify they're listed
- Refresh the dashboard page
- Check browser console for errors (F12)

### Prices not updating
- Check backend is running (should see logs)
- Verify internet connection
- Check Finnhub API status

### "Failed to load holdings" error
- Restart backend server
- Check [portfolio.json](portfolio.json) file exists
- Verify permissions on the file

## Summary

While Moomoo Malaysia doesn't support automatic API sync, this manual system still gives you:
- 📊 **Real-time portfolio tracking**
- 💹 **Live P&L calculations**
- 📈 **Market data and insights**
- 🤖 **AI financial advisor**

All you need to do is enter your holdings once and update them when you trade!

---

**Questions?** Check the main README or open an issue on GitHub.
