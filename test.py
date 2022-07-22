import pybit
from pybit import usdt_perpetual, exceptions

session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key="CRQIAjML2aykFyjnAF",
    api_secret="G0wIXLbDKrEYKWBuU9csBp0uRR8hqX2hU0G1"
)

print(session_auth.place_conditional_order(
    symbol="AVAXUSDT",
    order_type="Market",
    side="Buy",
    qty=10.1,
    base_price=24.100,
    stop_px=24.134,
    time_in_force="GoodTillCancel",
    trigger_by="LastPrice",
    reduce_only=False,
    close_on_trigger=False,
    position_idx=0
))
