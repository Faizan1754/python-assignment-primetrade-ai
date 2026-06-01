from decimal import Decimal, InvalidOperation


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


class ValidationError(Exception):
    pass


def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if not s:
        raise ValidationError("Symbol can't be empty.")
    if not s.isalpha():
        raise ValidationError(f"Symbol '{s}' looks off — should be something like BTCUSDT.")
    return s


def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValidationError(f"Side must be BUY or SELL, got '{side}'.")
    return s


def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type '{order_type}' isn't supported. Pick from: {', '.join(VALID_ORDER_TYPES)}."
        )
    return t


def validate_quantity(qty_str: str) -> Decimal:
    try:
        qty = Decimal(str(qty_str))
    except InvalidOperation:
        raise ValidationError(f"Quantity '{qty_str}' isn't a valid number.")
    if qty <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    return qty


def validate_price(price_str: str) -> Decimal:
    try:
        price = Decimal(str(price_str))
    except InvalidOperation:
        raise ValidationError(f"Price '{price_str}' isn't a valid number.")
    if price <= 0:
        raise ValidationError("Price must be greater than zero.")
    return price


def validate_order_inputs(symbol, side, order_type, quantity, price=None, stop_price=None):
    """
    Run all validations and return a clean dict ready to pass to the order layer.
    Raises ValidationError with a clear message if anything looks wrong.
    """
    result = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }

    if result["order_type"] == "LIMIT":
        if price is None:
            raise ValidationError("Limit orders need a price.")
        result["price"] = validate_price(price)

    if result["order_type"] == "STOP_MARKET":
        if stop_price is None:
            raise ValidationError("Stop-market orders need a stop price.")
        result["stop_price"] = validate_price(stop_price)

    return result
