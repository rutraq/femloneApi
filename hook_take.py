import ast
import time
from pybit import usdt_perpetual
from flask import Flask, request
from threading import Thread
import telebot
from datetime import datetime

app = Flask(__name__)


@app.route("/webHookReceive", methods=["POST"])
def make_order():
    strings = request.data.decode()
    if strings[0] == "{":
        hook = ast.literal_eval(strings)
        telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", strings)
        th = Thread(target=ByBit, args=(hook,))
        try:
            th.start()
        except Exception as err:
            record_exceptions(err)
    return "200"


class ByBit:
    def __init__(self, hook):
        self.position = hook["Position"]
        self.multi_take = hook["Multi Take"]
        self.symbol = hook["Symbol"]
        self.order = hook["Order"]
        self.entry_price = hook["Entry Price"]
        self.stop_loss_price = hook["Stop Loss Price"]
        self.stop_loss_two_price = hook["Stop Loss Two Price"]
        self.take_profit_price = hook["Take Profit Price"]
        self.take_profit_two_price = hook["Take Profit Two Price"]
        self.take_profit_three_price = hook["Take Profit Three Price"]
        self.leverage = hook["Leverage"]
        self.close_volume_first = hook["Close Volume First"]
        self.close_volume_second = hook["Close Volume Second"]
        self.close_volume_three = hook["Close Volume Three"]
        self.percent_balance = hook["Percent Balance"]
        self.api_key = hook["Api Key"]
        self.secret_api_key = hook["Secret Api Key"]
        self.session_auth = usdt_perpetual.HTTP(endpoint="https://api-testnet.bybit.com", api_key=self.api_key,
                                                api_secret=self.secret_api_key)
        self.set_leverage()
        self.open_trade()

    def set_leverage(self):
        self.session_auth.cross_isolated_margin_switch(
            symbol=self.symbol,
            is_isolated=True,
            buy_leverage=self.leverage,
            sell_leverage=self.leverage
        )

    # получаем данные о балансе и вычисляем объем ордера
    def balance_volume(self):
        wallet_balance = self.session_auth.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
        last_price = self.session_auth.orderbook(symbol=self.symbol)['result'][0]['price']
        order_balance = float(wallet_balance) * (float(self.percent_balance) / 100) * int(self.leverage)
        order_size = float(order_balance) / float(last_price)
        return order_size

    def open_trade(self):
        qty_order = round(self.balance_volume(), 3)
        self.session_auth.place_active_order(
            symbol=self.symbol,
            side=self.order,
            order_type="Market",
            qty=qty_order,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False,
            position_idx=0
        )
        self.tp_sl_profit(qty_order)

    def tp_sl_profit(self, qty_order):
        self.session_auth.set_trading_stop(
            symbol=self.symbol,
            side=self.order,
            take_profit=float(self.take_profit_price),
            stop_loss=float(self.stop_loss_price),
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tp_size=qty_order,
            sl_size=qty_order,
            position_idx=0
        )


@app.route("/check", methods=["GET"])
def check():
    return "everything is all right"


def record_exceptions(err):
    now = datetime.today().strftime("%d-%m-%Y %H:%M")
    telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335",
                                                                                   "Новая ошибка на сервере!")
    with open("errors.txt", 'w+') as file:
        error = "{0}  {1}\n".format(now, err)
        file.write(error)


if __name__ == "__main__":
    app.run()
