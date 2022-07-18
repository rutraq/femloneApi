from pybit import usdt_perpetual

hook = {"Position": "Open Short Position", "Multi Take": "true", "Symbol": "AVAXUSDT", "Order": "Sell",
        "Entry Price": "21800", "Stop Loss Price": "22000", "Stop Loss Two Price": "21000.55",
        "Take Profit Price": "20000.44", "Take Profit Two Price": "19000",
        "Take Profit Three Price": "18000", "Leverage": "20", "Close Volume First": "20",
        "Close Volume Second": "50", "Close Volume Three": "100", "Percent Balance": "2.5", "Api Key": "CRQIAjML2aykFyjnAF", "Secret Api Key": "G0wIXLbDKrEYKWBuU9csBp0uRR8hqX2hU0G1"}

position = hook["Position"]
multi_take = hook["Multi Take"]
symbol = hook["Symbol"]
order = hook["Order"]
entry_price = hook["Entry Price"]
stop_loss_price = hook["Stop Loss Price"]
stop_loss_two_price = hook["Stop Loss Two Price"]
take_profit_price = hook["Take Profit Price"]
take_profit_two_price = hook["Take Profit Two Price"]
take_profit_three_price = hook["Take Profit Three Price"]
leverage = hook["Leverage"]
close_volume_first = hook["Close Volume First"]
close_volume_second = hook["Close Volume Second"]
close_volume_three = hook["Close Volume Three"]
percent_balance = hook["Percent Balance"]
api_key = hook["Api Key"]
secret_api_key = hook["Secret Api Key"]


session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key=api_key,
    api_secret=secret_api_key
)



session_auth.full_partial_position_tp_sl_switch(
            symbol=symbol,
            tp_sl_mode="Partial"
            )
