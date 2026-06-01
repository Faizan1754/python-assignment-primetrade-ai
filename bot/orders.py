"""
Order placement logic.

Sits between the CLI and the raw API client.  Does the translation from
our internal validated dict → Binance API params, then makes the call
and returns something clean for the CLI to print.
"""

import logging
from decimal import Decimal

from .client import BinanceClient, BinanceAPIError

logger = logging.getLogger("trading_bot.orders")


def _fmt(value) -> str:
    """Format a Decimal for the API — drop trailing zeros."""
    return format(Decimal(str(value)).normalize(), "f")


def place_market_order(client: BinanceClient, symbol: str, side: str, quantity: Decimal) -> dict:
    logger.info("Placing MARKET %s %s qty=%s", side, symbol, quantity)

    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": _fmt(quantity),
    }

    try:
        resp = client.place_order(**params)
    except BinanceAPIError as e:
        logger.error("Order rejected by Binance — %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error placing market order — %s", e)
        raise

    logger.info(
        "Market order placed — orderId=%s status=%s executedQty=%s avgPrice=%s",
        resp.get("orderId"),
        resp.get("status"),
        resp.get("executedQty"),
        resp.get("avgPrice"),
    )
    return resp


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    time_in_force: str = "GTC",
) -> dict:
    logger.info(
        "Placing LIMIT %s %s qty=%s price=%s tif=%s",
        side, symbol, quantity, price, time_in_force,
    )

    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "quantity": _fmt(quantity),
        "price": _fmt(price),
        "timeInForce": time_in_force,
    }

    try:
        resp = client.place_order(**params)
    except BinanceAPIError as e:
        logger.error("Order rejected by Binance — %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error placing limit order — %s", e)
        raise

    logger.info(
        "Limit order placed — orderId=%s status=%s",
        resp.get("orderId"),
        resp.get("status"),
    )
    return resp


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_price: Decimal,
) -> dict:
    """
    STOP_MARKET — triggers a market order once the price hits stop_price.
    Handy for cutting losses without having to babysit the screen.
    """
    logger.info(
        "Placing STOP_MARKET %s %s qty=%s stopPrice=%s",
        side, symbol, quantity, stop_price,
    )

    params = {
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "quantity": _fmt(quantity),
        "stopPrice": _fmt(stop_price),
    }

    try:
        resp = client.place_order(**params)
    except BinanceAPIError as e:
        logger.error("Stop-market order rejected — %s", e)
        raise
    except Exception as e:
        logger.error("Unexpected error placing stop-market order — %s", e)
        raise

    logger.info(
        "Stop-market order placed — orderId=%s status=%s",
        resp.get("orderId"),
        resp.get("status"),
    )
    return resp


def dispatch_order(client: BinanceClient, validated: dict) -> dict:
    """
    Takes the clean dict from validators.validate_order_inputs and routes
    to the right placement function.  Returns the raw Binance response.
    """
    otype = validated["order_type"]

    if otype == "MARKET":
        return place_market_order(
            client,
            symbol=validated["symbol"],
            side=validated["side"],
            quantity=validated["quantity"],
        )

    if otype == "LIMIT":
        return place_limit_order(
            client,
            symbol=validated["symbol"],
            side=validated["side"],
            quantity=validated["quantity"],
            price=validated["price"],
        )

    if otype == "STOP_MARKET":
        return place_stop_market_order(
            client,
            symbol=validated["symbol"],
            side=validated["side"],
            quantity=validated["quantity"],
            stop_price=validated["stop_price"],
        )

    # shouldn't get here given validator, but just in case
    raise ValueError(f"Unknown order type: {otype}")
