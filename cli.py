#!/usr/bin/env python3
"""
cli.py — entry point for the trading bot.

Usage examples are in README.md, but the short version:

  python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --qty 0.01 --price 3000
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 58000
"""

import argparse
import os
import sys

from bot.client import BinanceClient, BinanceAPIError
from bot.logging_config import setup_logging
from bot.orders import dispatch_order
from bot.validators import ValidationError, validate_order_inputs

logger = setup_logging()


# ------------------------------------------------------------------ #
# output helpers                                                       #
# ------------------------------------------------------------------ #

def _separator():
    print("─" * 52)


def print_request_summary(args):
    _separator()
    print("  ORDER REQUEST SUMMARY")
    _separator()
    print(f"  Symbol     : {args.symbol.upper()}")
    print(f"  Side       : {args.side.upper()}")
    print(f"  Type       : {args.type.upper()}")
    print(f"  Quantity   : {args.qty}")
    if args.price:
        print(f"  Price      : {args.price}")
    if args.stop_price:
        print(f"  Stop Price : {args.stop_price}")
    _separator()


def print_order_response(resp: dict):
    _separator()
    print("  ORDER RESPONSE")
    _separator()
    print(f"  Order ID   : {resp.get('orderId', 'n/a')}")
    print(f"  Status     : {resp.get('status', 'n/a')}")
    print(f"  Executed   : {resp.get('executedQty', '0')}")
    avg = resp.get("avgPrice") or resp.get("price") or "n/a"
    print(f"  Avg Price  : {avg}")
    print(f"  Client OID : {resp.get('clientOrderId', 'n/a')}")
    _separator()


# ------------------------------------------------------------------ #
# arg parsing                                                          #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    p.add_argument("--symbol", required=True, help="e.g. BTCUSDT")
    p.add_argument("--side", required=True, help="BUY or SELL")
    p.add_argument(
        "--type", required=True, dest="type",
        help="MARKET, LIMIT, or STOP_MARKET",
    )
    p.add_argument("--qty", required=True, help="Order quantity")
    p.add_argument("--price", default=None, help="Limit price (required for LIMIT)")
    p.add_argument("--stop-price", default=None, dest="stop_price",
                   help="Stop price (required for STOP_MARKET)")
    return p


# ------------------------------------------------------------------ #
# main                                                                 #
# ------------------------------------------------------------------ #

def main():
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        print(
            "\n  Error: BINANCE_API_KEY and BINANCE_API_SECRET env vars must be set.\n"
            "  Export them before running:\n\n"
            "    export BINANCE_API_KEY=your_key\n"
            "    export BINANCE_API_SECRET=your_secret\n"
        )
        sys.exit(1)

    # show what we're about to do before we do it
    print_request_summary(args)

    # validate — bail out early with a clean message if something's off
    try:
        validated = validate_order_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.qty,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as e:
        print(f"\n  Validation error: {e}\n")
        logger.warning("Validation failed: %s", e)
        sys.exit(1)

    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    try:
        resp = dispatch_order(client, validated)
    except BinanceAPIError as e:
        print(f"\n  Binance rejected the order: {e.msg}  (code {e.code})\n")
        logger.error("BinanceAPIError: %s", e)
        sys.exit(1)
    except Exception as e:
        print(f"\n  Something went wrong: {e}\n")
        logger.exception("Unhandled exception during order placement")
        sys.exit(1)

    print_order_response(resp)
    print("\n  ✓ Order placed successfully.\n")
    logger.info("Done — orderId=%s", resp.get("orderId"))


if __name__ == "__main__":
    main()
