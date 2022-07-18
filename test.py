import pybit
from pybit import usdt_perpetual, exceptions

session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key="CRQIAjML2aykFyjnAF",
    api_secret="G0wIXLbDKrEYKWBuU9csBp0uRR8hqX2hU0G1"
)

check_tp_sl = session_auth.my_position(symbol="NEARUSDT")

check_tp_sl = check_tp_sl['result'][0]['tp_sl_mode'] + " Mode"
print(check_tp_sl)
# try:
#     print(session_auth.set_leverage(
#         symbol="NEARUSDT",
#         buy_leverage=20,
#         sell_leverage=20
#     ))
# except exceptions.InvalidRequestError:
#     print("Плечо уже установленно")
#
# try:
#     print(session_auth.cross_isolated_margin_switch(
#         symbol="NEARUSDT",
#         is_isolated=False,
#         buy_leverage=20,
#         sell_leverage=20
#     ))
# except exceptions.InvalidRequestError:
#     print("Мод уже установлен")
#
#
#
# print(session_auth.full_partial_position_tp_sl_switch(
#     symbol="NEARUSDT",
#     tp_sl_mode="Partial"
# ))
#
#
#
# try:
#     print(session_auth.position_mode_switch(
#         symbol="NEARUSDT",
#         mode="MergedSingle"
#     ))
# except exceptions.InvalidRequestError:
#     print("Мод уже установлен")