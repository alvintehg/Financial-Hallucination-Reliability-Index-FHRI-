# Moomoo OpenD Integration - Complete Setup Guide

## Overview

This guide will help you connect your application to Moomoo OpenD API for automatic portfolio syncing.

## Prerequisites

1. **Moomoo Desktop Application** installed
2. **Moomoo account** with some positions
3. **OpenD enabled** in Moomoo settings

## Step-by-Step Setup

### Step 1: Enable Moomoo OpenD

1. Open Moomoo desktop application
2. Go to **Settings** → **API** → **OpenD**
3. Enable OpenD with these settings:
   - **IP**: `127.0.0.1`
   - **Port**: `11111`
   - **Log Level**: `info`
   - **Language**: `English`
4. Click **Save** and ensure OpenD status shows "Running"

### Step 2: Install Required Package

The moomoo-api package has already been added to requirements.txt. To install:

```bash
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"
pip install moomoo-api
```

### Step 3: Test Connection

Run the test script to verify Moomoo OpenD connection:

```bash
python src/moomoo_integration.py
```

You should see:
```
✓ Success! Found X positions:
  - AAPL: 50 shares @ $150.00
    Market Value: $9,000.00 | P&L: $750.00
```

### Step 4: Sync Your Portfolio

You have three options to sync:

#### Option A: Via Backend API (Recommended)

1. **Start the backend**:
   ```bash
   python -m uvicorn src.server:app --port 8000 --reload
   ```

2. **Trigger sync via HTTP**:
   ```bash
   curl -X POST http://127.0.0.1:8000/moomoo/sync
   ```

   Or open in browser: http://127.0.0.1:8000/moomoo/sync

3. **Check positions**:
   ```bash
   curl http://127.0.0.1:8000/moomoo/positions
   ```

#### Option B: Via Python Script

```python
from src.moomoo_integration import MoomooIntegration

with MoomooIntegration() as moomoo:
    success = moomoo.sync_to_portfolio_json()
    if success:
        print("✓ Portfolio synced!")
```

#### Option C: Manual One-Time Sync

```bash
# Navigate to project
cd "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot"

# Run the integration script
python -c "from src.moomoo_integration import MoomooIntegration; m = MoomooIntegration(); m.connect(); m.sync_to_portfolio_json(); m.disconnect()"
```

### Step 5: Verify Sync

Check that `portfolio.json` has been updated:

```bash
# View the synced portfolio
cat portfolio.json
```

You should see:
```json
{
  "holdings": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "shares": 50.0,
      "cost_basis": 150.0,
      "asset_type": "equity"
    }
  ],
  "last_updated": "2025-01-05T10:30:00Z",
  "synced_from": "moomoo",
  "sync_method": "opend_api"
}
```

### Step 6: Restart Backend & View Live Portfolio

1. **Restart backend** (to load new portfolio.json):
   ```bash
   python -m uvicorn src.server:app --port 8000 --reload
   ```

2. **Open frontend** (if not already running):
   ```bash
   cd frontend
   npm start
   ```

3. **View dashboard**: Navigate to http://localhost:3000/dashboard

Your portfolio will now show:
- ✅ **Real positions** from Moomoo
- ✅ **Live market prices** from Finnhub
- ✅ **Calculated P&L** based on your cost basis
- ✅ **Auto-refresh** every 30 seconds

## Available API Endpoints

### GET /moomoo/positions
Fetch current positions from Moomoo.

**Response:**
```json
{
  "status": "success",
  "positions": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "shares": 50.0,
      "market_value": 9000.0,
      "cost_basis": 150.0,
      "current_price": 180.0,
      "unrealized_pnl": 1500.0,
      "unrealized_pnl_pct": 20.0
    }
  ],
  "count": 1
}
```

### GET /moomoo/account
Fetch account information.

**Response:**
```json
{
  "status": "success",
  "cash": 10000.0,
  "total_assets": 50000.0,
  "market_value": 40000.0,
  "currency": "USD"
}
```

### POST /moomoo/sync
Sync Moomoo positions to portfolio.json.

**Response:**
```json
{
  "status": "success",
  "message": "Portfolio synced successfully",
  "positions_synced": 5,
  "positions": [...]
}
```

## Automatic Syncing (Optional)

To sync automatically every X minutes, you have two options:

### Option 1: Cron Job (Linux/Mac) or Task Scheduler (Windows)

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create new task
3. Trigger: Every 5 minutes
4. Action: Run script
   ```
   python "C:\Users\User\OneDrive\Documents\FYP 1\llm-fin-chatbot\scripts\sync_moomoo.py"
   ```

Create `scripts/sync_moomoo.py`:
```python
from src.moomoo_integration import MoomooIntegration

if __name__ == "__main__":
    with MoomooIntegration() as moomoo:
        success = moomoo.sync_to_portfolio_json()
        print(f"Sync {'successful' if success else 'failed'}")
```

### Option 2: Frontend Sync Button

Add a "Sync with Moomoo" button to your dashboard that calls:
```javascript
await axios.post('http://127.0.0.1:8000/moomoo/sync');
```

## Troubleshooting

### Connection Failed

**Error**: `Failed to connect to Moomoo OpenD`

**Solutions**:
1. Verify Moomoo desktop app is running
2. Check OpenD is enabled in Settings
3. Confirm host=127.0.0.1, port=11111
4. Try restarting Moomoo app

### No Positions Returned

**Error**: `No positions found`

**Solutions**:
1. Check you have open positions in Moomoo
2. Verify you're logged into correct account
3. Check market hours (positions might not show after hours)

### Import Error

**Error**: `No module named 'moomoo'`

**Solution**:
```bash
pip install moomoo-api
```

### Permission Denied

**Error**: `unlock_trade failed`

**Solution**:
- The trade password is optional for reading positions
- You can ignore this warning if you're only syncing portfolio
- To enable trading features, set password in code:
  ```python
  ret, data = ctx.unlock_trade("YOUR_PASSWORD")
  ```

## Data Flow Diagram

```
┌─────────────────┐
│  Moomoo OpenD   │  (Port 11111)
│  Running in     │
│  Desktop App    │
└────────┬────────┘
         │
         │ TCP Connection
         │
┌────────▼──────────────────────────────────────┐
│  MoomooIntegration Service                    │
│  - Connects to OpenD                          │
│  - Fetches positions via API                  │
│  - Converts to portfolio.json format          │
└────────┬──────────────────────────────────────┘
         │
         │ Writes to
         │
┌────────▼─────────┐
│  portfolio.json  │ (Synced holdings)
└────────┬─────────┘
         │
         │ Read by
         │
┌────────▼──────────────────────────────────────┐
│  PortfolioService                             │
│  - Reads portfolio.json                       │
│  - Fetches live prices from Finnhub           │
│  - Calculates P&L and allocations             │
└────────┬──────────────────────────────────────┘
         │
         │ API Response
         │
┌────────▼────────────┐
│  Dashboard Frontend │
│  - Displays live    │
│  - Auto-refreshes   │
└─────────────────────┘
```

## Security Notes

- OpenD only accepts connections from localhost (127.0.0.1)
- No passwords are stored in code
- API credentials stay on your machine
- Portfolio data is local only

## Next Steps

1. ✅ Test connection
2. ✅ Sync portfolio once
3. ✅ Verify dashboard shows correct data
4. ⏳ Set up automatic syncing (optional)
5. ⏳ Add sync button to UI (optional)

## Support

- **Moomoo OpenD Docs**: https://openapi.moomoo.com/
- **moomoo-api GitHub**: https://github.com/FutunnOpen/py-futu-api

Enjoy automatic portfolio syncing! 🚀
