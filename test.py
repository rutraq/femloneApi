from pybit import usdt_perpetual

hook = {"Position": "Open Short Position", "Multi Take": "true", "Symbol": "BTCUSDT", "Order": "Sell",
        "Entry Price": "21800", "Stop Loss Price": "22000", "Stop Loss Two Price": "21000.55",
        "Take Profit Price": "20000.44", "Take Profit Two Price": "19000",
        "Take Profit Three Price": "18000", "Leverage": "10", "Close Volume First": "20",
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


def set_leverage(symbol, leverage):
        session_auth.cross_isolated_margin_switch(
                symbol=symbol,
                buy_leverage=leverage,
                sell_leverage=leverage
        )


# получаем данные о балансе и вычисляем объем ордера
def balance_volume(symbol, percent_balance, leverage):
        wallet_balance = session_auth.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
        last_price = session_auth.orderbook(symbol=symbol)['result'][0]['price']
        order_balance = float(wallet_balance) * (float(percent_balance)/100) * int(leverage)
        order_size = float(order_balance) / float(last_price)
        print(order_size)
        return order_size


# открываем позицию
def open_trade(symbol, order, percent_balance, leverage, take_profit_price, stop_loss_price):
        qty_order = round(balance_volume(symbol, percent_balance, leverage), 3)
        session_auth.place_active_order(
                symbol=symbol,
                side=order,
                order_type="Market",
                qty=qty_order,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False,
                position_idx=0
        )
        tp_sl_profit(symbol, order, take_profit_price, stop_loss_price, qty_order)


# установка тейк профита и стоп лосса
def tp_sl_profit(symbol, order, take_profit_price, stop_loss_price, qty_order):
        session_auth.set_trading_stop(
            symbol=symbol,
            side=order,
            take_profit=float(take_profit_price),
            stop_loss=float(stop_loss_price),
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tp_size=qty_order,
            sl_size=qty_order,
            position_idx=0
        )


set_leverage(symbol, leverage)
open_trade(symbol, order, percent_balance, leverage, take_profit_price, stop_loss_price)
