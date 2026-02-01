"""Position sizing calculator for forex trading.

This module provides utilities for calculating appropriate position sizes
based on account equity, risk percentage, and stop loss distance.

Example:
    >>> # Calculate risk amount
    >>> risk_amount = calculate_risk_amount(account_equity=10000, risk_percent=1.0)
    >>> print(f"Risk amount: ${risk_amount}")
    Risk amount: $100.0

    >>> # Calculate position size
    >>> lots = calculate_position_size(
    ...     account_equity=10000,
    ...     risk_percent=1.0,
    ...     stop_loss_pips=20,
    ...     pip_value=10
    ... )
    >>> print(f"Position size: {lots} lots")
    Position size: 0.5 lots

    >>> # Get pip value for a specific instrument
    >>> pip_val = get_pip_value("EUR_USD")
    >>> print(f"EUR_USD pip value: ${pip_val}")
    EUR_USD pip value: $10

    >>> # Convert between pips and price
    >>> price = pips_to_price(20, "EUR_USD")
    >>> print(f"20 pips = {price} price distance")
    20 pips = 0.002 price distance

    >>> pips = price_to_pips(0.002, "EUR_USD")
    >>> print(f"0.002 price = {pips} pips")
    0.002 price = 20.0 pips
"""

from typing import Optional, Dict

# Pip conversion constants (how many decimal places = 1 pip)
PIP_CONVERSIONS: Dict[str, int] = {
    "EUR_USD": 4,  # 0.0001 = 1 pip
    "GBP_USD": 4,  # 0.0001 = 1 pip
    "AUD_USD": 4,  # 0.0001 = 1 pip
    "NZD_USD": 4,  # 0.0001 = 1 pip
    "USD_JPY": 2,  # 0.01 = 1 pip
    "USD_CHF": 4,  # 0.0001 = 1 pip
    "USD_CAD": 4,  # 0.0001 = 1 pip
    "EUR_GBP": 4,  # 0.0001 = 1 pip
    "EUR_JPY": 2,  # 0.01 = 1 pip
}

# Pip values per standard lot (100,000 units) in USD
PIP_VALUES: Dict[str, float] = {
    "EUR_USD": 10.0,  # $10 per pip per standard lot
    "GBP_USD": 10.0,  # $10 per pip per standard lot
    "AUD_USD": 10.0,  # $10 per pip per standard lot
    "NZD_USD": 10.0,  # $10 per pip per standard lot
    "USD_JPY": 9.12,  # Variable, ~$9.12 per pip per standard lot
    "USD_CHF": 10.15,  # Variable, ~$10.15 per pip per standard lot
    "USD_CAD": 10.0,  # ~$10 per pip per standard lot
    "EUR_GBP": 10.0,  # ~$10 per pip per standard lot
    "EUR_JPY": 9.12,  # Variable, ~$9.12 per pip per standard lot
}


def validate_risk_percent(risk_percent: float) -> None:
    """Validate risk percentage is within acceptable range.

    Args:
        risk_percent: Risk percentage to validate (0-100)

    Raises:
        ValueError: If risk_percent is not between 0 and 100
    """
    if not (0 < risk_percent <= 100):
        raise ValueError(f"Risk percent must be between 0 and 100, got {risk_percent}")


def validate_positive(value: float, name: str) -> None:
    """Validate that a value is positive.

    Args:
        value: Value to validate
        name: Name of the parameter for error messages

    Raises:
        ValueError: If value is not positive
    """
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def calculate_risk_amount(account_equity: float, risk_percent: float) -> float:
    """Calculate the dollar amount to risk based on account equity and risk percentage.

    This is the first step in position sizing: determining how much money
    you're willing to risk on a single trade.

    Args:
        account_equity: Current account equity in USD
        risk_percent: Percentage of account to risk per trade (0-100)

    Returns:
        float: Dollar amount to risk on the trade

    Raises:
        ValueError: If account_equity is not positive or risk_percent is invalid

    Example:
        >>> risk_amount = calculate_risk_amount(account_equity=10000, risk_percent=1.0)
        >>> print(f"Risk: ${risk_amount}")
        Risk: $100.0

        >>> risk_amount = calculate_risk_amount(account_equity=50000, risk_percent=2.5)
        >>> print(f"Risk: ${risk_amount}")
        Risk: $1250.0
    """
    validate_positive(account_equity, "account_equity")
    validate_risk_percent(risk_percent)

    return account_equity * risk_percent / 100.0


def get_pip_value(instrument: str, account_currency: str = "USD") -> float:
    """Get the pip value for a forex instrument per standard lot.

    Returns the value of one pip for a standard lot (100,000 units) of the
    specified currency pair. Most major pairs have a pip value of ~$10 when
    the account is denominated in USD.

    Args:
        instrument: Currency pair (e.g., "EUR_USD", "GBP_USD", "USD_JPY")
        account_currency: Account base currency (currently only USD supported)

    Returns:
        float: Pip value in account currency for a standard lot

    Raises:
        ValueError: If instrument is not supported

    Example:
        >>> pip_val = get_pip_value("EUR_USD")
        >>> print(f"EUR_USD: ${pip_val}/pip")
        EUR_USD: $10.0/pip

        >>> pip_val = get_pip_value("USD_JPY")
        >>> print(f"USD_JPY: ${pip_val}/pip")
        USD_JPY: $9.12/pip
    """
    if instrument not in PIP_VALUES:
        available = ", ".join(sorted(PIP_VALUES.keys()))
        raise ValueError(
            f"Instrument '{instrument}' not supported. Available: {available}"
        )

    if account_currency != "USD":
        raise ValueError(
            f"Account currency '{account_currency}' not yet supported. "
            f"Only 'USD' is supported."
        )

    return PIP_VALUES[instrument]


def pips_to_price(pips: float, instrument: str) -> float:
    """Convert pip distance to price distance.

    Converts a number of pips to the actual price difference for a given
    currency pair. This depends on the pip size of the instrument.

    Args:
        pips: Number of pips
        instrument: Currency pair (e.g., "EUR_USD", "USD_JPY")

    Returns:
        float: Price distance (e.g., 20 pips for EUR_USD = 0.002)

    Raises:
        ValueError: If instrument is not supported

    Example:
        >>> # EUR_USD has 4 decimal places (0.0001 = 1 pip)
        >>> price = pips_to_price(20, "EUR_USD")
        >>> print(f"20 pips = {price}")
        20 pips = 0.002

        >>> # USD_JPY has 2 decimal places (0.01 = 1 pip)
        >>> price = pips_to_price(20, "USD_JPY")
        >>> print(f"20 pips = {price}")
        20 pips = 0.2
    """
    if instrument not in PIP_CONVERSIONS:
        available = ", ".join(sorted(PIP_CONVERSIONS.keys()))
        raise ValueError(
            f"Instrument '{instrument}' not supported. Available: {available}"
        )

    decimal_places = PIP_CONVERSIONS[instrument]
    pip_size = 10 ** (-decimal_places)
    return pips * pip_size


def price_to_pips(price_distance: float, instrument: str) -> float:
    """Convert price distance to pip count.

    Converts a price difference to the number of pips for a given
    currency pair. This is the inverse of pips_to_price().

    Args:
        price_distance: Price difference (e.g., 0.002 for EUR_USD)
        instrument: Currency pair (e.g., "EUR_USD", "USD_JPY")

    Returns:
        float: Number of pips

    Raises:
        ValueError: If instrument is not supported

    Example:
        >>> # EUR_USD has 4 decimal places
        >>> pips = price_to_pips(0.002, "EUR_USD")
        >>> print(f"0.002 price = {pips} pips")
        0.002 price = 20.0 pips

        >>> # USD_JPY has 2 decimal places
        >>> pips = price_to_pips(0.2, "USD_JPY")
        >>> print(f"0.2 price = {pips} pips")
        0.2 price = 20.0 pips
    """
    if instrument not in PIP_CONVERSIONS:
        available = ", ".join(sorted(PIP_CONVERSIONS.keys()))
        raise ValueError(
            f"Instrument '{instrument}' not supported. Available: {available}"
        )

    decimal_places = PIP_CONVERSIONS[instrument]
    pip_size = 10 ** (-decimal_places)
    return price_distance / pip_size


def calculate_position_size(
    account_equity: float,
    risk_percent: float,
    stop_loss_pips: float,
    pip_value: Optional[float] = None,
    instrument: Optional[str] = None,
) -> float:
    """Calculate appropriate position size for a forex trade.

    Uses the formula:
        Position Size (lots) = Risk Amount / (Stop Loss in Pips × Pip Value)

    Where Risk Amount = Account Equity × Risk % / 100

    This function returns position size in terms of standard lots (100,000 units).
    For example, 0.5 lots = 50,000 units, 0.1 lots = 10,000 units (mini lot).

    Args:
        account_equity: Current account equity in USD
        risk_percent: Percentage of account to risk per trade (0-100)
        stop_loss_pips: Distance to stop loss in pips
        pip_value: Pip value per standard lot in USD (optional if instrument provided)
        instrument: Currency pair to look up pip_value (optional if pip_value provided)

    Returns:
        float: Position size in standard lots (rounded to 2 decimal places)

    Raises:
        ValueError: If inputs are invalid or both pip_value and instrument are missing
        TypeError: If pip_value is not numeric

    Example:
        >>> # Method 1: Provide pip_value directly
        >>> lots = calculate_position_size(
        ...     account_equity=10000,
        ...     risk_percent=1.0,
        ...     stop_loss_pips=20,
        ...     pip_value=10
        ... )
        >>> print(f"Position size: {lots} lots")
        Position size: 0.5 lots

        >>> # Method 2: Use instrument name to look up pip_value
        >>> lots = calculate_position_size(
        ...     account_equity=10000,
        ...     risk_percent=1.0,
        ...     stop_loss_pips=20,
        ...     instrument="EUR_USD"
        ... )
        >>> print(f"Position size: {lots} lots")
        Position size: 0.5 lots

        >>> # Larger position with bigger risk
        >>> lots = calculate_position_size(
        ...     account_equity=50000,
        ...     risk_percent=2.0,
        ...     stop_loss_pips=50,
        ...     instrument="GBP_USD"
        ... )
        >>> print(f"Position size: {lots} lots")
        Position size: 2.0 lots
    """
    # Validate inputs
    validate_positive(account_equity, "account_equity")
    validate_risk_percent(risk_percent)
    validate_positive(stop_loss_pips, "stop_loss_pips")

    # Determine pip_value
    if pip_value is None and instrument is None:
        raise ValueError("Either 'pip_value' or 'instrument' must be provided")

    if pip_value is None:
        pip_value = get_pip_value(instrument)
    else:
        validate_positive(pip_value, "pip_value")

    # Calculate position size
    risk_amount = calculate_risk_amount(account_equity, risk_percent)
    position_size = risk_amount / (stop_loss_pips * pip_value)

    # Round to 2 decimal places (nearest 0.01 lot = 1000 units)
    return round(position_size, 2)
