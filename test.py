import pybit
from pybit import usdt_perpetual, exceptions

session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key="CRQIAjML2aykFyjnAF",
    api_secret="G0wIXLbDKrEYKWBuU9csBp0uRR8hqX2hU0G1"
)


# print(session_auth.place_conditional_order(
#     symbol="BTCUSDT",
#     order_type="Market",
#     side="Sell",
#     qty=0.015,
#     base_price=23000,
#     stop_px=21800.8,
#     time_in_force="GoodTillCancel",
#     trigger_by="LastPrice",
#     reduce_only=False,
#     order_link_id="BTCUSDT-StopLoss",
#     close_on_trigger=False,
#     position_idx=0
# ))

print(session_auth.cancel_conditional_order(
    symbol="BTCUSDT",
    order_link_id="BTCUSDT-StopLoss"
))
