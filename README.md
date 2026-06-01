# Binance Futures Testnet Trading Bot

A small Python CLI tool that places orders on [Binance Futures Testnet](https://testnet.binancefuture.com).  
Supports Market, Limit, and Stop-Market orders.

---

## Setup

**1. Clone / unzip the project**

```bash
cd trading_bot
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

Only one external library is used: `requests`.

**3. Get testnet API keys**

- Register at https://testnet.binancefuture.com  
- Go to **API Keys** in the top-right menu  
- Generate a key pair and save them somewhere safe

**4. Export your keys as environment variables**

```bash
export BINANCE_API_KEY=your_api_key_here
export BINANCE_API_SECRET=your_api_secret_here
```

On Windows (Command Prompt):
```
set BINANCE_API_KEY=your_api_key_here
set BINANCE_API_SECRET=your_api_secret_here
```

---

## Running the bot

### Market order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### Limit order

```bash
python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3800
```

### Stop-Market order (bonus order type)

Triggers a market order once the price hits your stop level — useful as a basic stop-loss.

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 58000
```

---

## What gets printed

```
────────────────────────────────────────────────────
  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
────────────────────────────────────────────────────
────────────────────────────────────────────────────
  ORDER RESPONSE
────────────────────────────────────────────────────
  Order ID   : 4029151
  Status     : FILLED
  Executed   : 0.001
  Avg Price  : 67823.10
  Client OID : web_abc123
────────────────────────────────────────────────────

  ✓ Order placed successfully.
```

---

## Logs

All requests, responses, and errors are logged to `logs/bot_YYYYMMDD.log`.  

- Console shows INFO and above (clean, one line per event)  
- Log file captures DEBUG too (full response bodies, params sent)

Sample log files are in the `logs/` folder:

| File | What it shows |
|---|---|
| `market_order_sample.log` | Successful MARKET BUY, filled immediately |
| `limit_order_sample.log` | LIMIT SELL placed, sitting as NEW |

---

## Project structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # signs requests, handles HTTP, raises BinanceAPIError
    orders.py          # market / limit / stop-market placement functions
    validators.py      # validates and coerces CLI input before it hits the API
    logging_config.py  # sets up file + console handlers
  cli.py               # argument parsing, output formatting, wires everything together
  requirements.txt
  logs/
    market_order_sample.log
    limit_order_sample.log
```

---

## Assumptions

- USDT-M futures only (testnet URL: `https://testnet.binancefuture.com`)
- Quantity precision isn't pre-checked against exchange filters — if Binance rejects the quantity, the error message from the API is shown as-is
- `timeInForce` for Limit orders defaults to `GTC` (Good Till Cancelled); not exposed as a CLI flag to keep the interface simple
- No `.env` file loading — keys are expected as real environment variables

---

## Error handling

| Situation | What happens |
|---|---|
| Missing/wrong side or type | Validation error printed before any API call is made |
| Zero or negative quantity | Validation error |
| Price missing for LIMIT | Validation error |
| Binance rejects the order | `BinanceAPIError` caught, code + message printed |
| Network timeout | Exception caught, message printed, exit code 1 |
| Missing API keys | Early exit with setup instructions |
# python-assignment-primetrade-ai
