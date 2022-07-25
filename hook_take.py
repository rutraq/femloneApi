import ast
import time
from pybit import usdt_perpetual, exceptions
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
        th = Thread(target=ByBit, args=(hook,))
        try:
            th.start()
        except Exception as err:
            record_exceptions(err)
    return "200"


class ByBit:
    def __init__(self, hook):
        self.position = hook["Position"]
        if self.position == "Open Short Position" or self.position == "Open Long Position":
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
            self.position_mode = hook["Position mode"]
            self.margin_mode = hook["Margin mode"]
            self.position_tp_mode = hook["Position TP/SL mode"]
            self.position_idx = 0
            self.base_price = hook["Base price"]
            self.base_price_second = hook["Base price second"]
            self.round_volume = hook["Round volume"]
            self.new_order = ""
            self.session_auth = usdt_perpetual.HTTP(endpoint="https://api.bybit.com", api_key=self.api_key,
                                                    api_secret=self.secret_api_key)
            self.set_position_idx()
            self.send_hook()

            try:
                self.set_position_mode()
            except exceptions.InvalidRequestError:
                pass
            try:
                self.set_margin_mode()
            except exceptions.InvalidRequestError:
                pass
            try:
                self.set_position_tp_sl_mode()
            except exceptions.FailedRequestError:
                pass
            try:
                self.set_leverage()
            except exceptions.InvalidRequestError:
                pass

            self.open_trade()

        if self.position == "Close Take Profit":
            self.symbol = hook["Symbol"]
            self.take_profit = hook["Take Profit"]
            self.move_tp = hook["Move TP"]
            self.stop_loss_two_price = hook["Stop Loss Two Price"]
            self.base_price_second = hook["Base price second"]
            self.side_order = hook["Side Order"]
            self.api_key = hook["Api Key"]
            self.secret_api_key = hook["Secret Api Key"]

            if self.take_profit == "TP3":
                self.cancel_sl()

            if self.take_profit == self.move_tp:
                self.cancel_sl()
                self.new_sl()

    # отправка хука в тг
    def send_hook(self):
        message = '''*Position* : {position}
*Multi Take* : {multi_take}
*Symbol* : {symbol}
*Order* : {order}
*Entry Price* : {entry_price}
*Stop Loss Price* : {stop_loss_1}
*Stop Loss Two Price* : {stop_loss_2}
*Take Profit Price* :  {take_profit_1} 
*Take Profit Two Price* :  {take_profit_2}
*Take Profit Three Price* :  {take_profit_3}
*Percent Balance*:  {percent}'''
        telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335",
                                                                                       message.format(
                                                                                           position=self.position,
                                                                                           multi_take=self.multi_take,
                                                                                           symbol=self.symbol,
                                                                                           order=self.order,
                                                                                           entry_price=self.entry_price,
                                                                                           stop_loss_1=self.stop_loss_price,
                                                                                           stop_loss_2=self.stop_loss_two_price,
                                                                                           take_profit_1=self.take_profit_price,
                                                                                           take_profit_2=self.take_profit_two_price,
                                                                                           take_profit_3=self.take_profit_three_price,
                                                                                           percent=self.percent_balance
                                                                                       ), parse_mode="Markdown")

    # установка плеча
    def set_leverage(self):
        self.session_auth.set_leverage(
            symbol=self.symbol,
            buy_leverage=self.leverage,
            sell_leverage=self.leverage
        )

    # установка режима позиции
    def set_position_mode(self):
        if self.position_mode == "One-Way Mode":
            self.session_auth.position_mode_switch(
                symbol=self.symbol,
                mode="MergedSingle"
            )

        elif self.position_mode == "Hedge Mode":
            self.session_auth.position_mode_switch(
                symbol=self.symbol,
                mode="BothSide"
            )

    # установка режима маржи
    def set_margin_mode(self):
        if self.margin_mode == "Isolated Mode":
            self.session_auth.cross_isolated_margin_switch(
                symbol=self.symbol,
                is_isolated=True,
                buy_leverage=self.leverage,
                sell_leverage=self.leverage
            )
        elif self.margin_mode == "Cross Mode":
            self.session_auth.cross_isolated_margin_switch(
                symbol=self.symbol,
                is_isolated=False,
                buy_leverage=self.leverage,
                sell_leverage=self.leverage
            )

    # Настройка TP/SL
    def set_position_tp_sl_mode(self):
        check_tp_sl = self.session_auth.my_position(symbol=self.symbol)
        check_tp_sl = check_tp_sl['result'][0]['tp_sl_mode'] + " Mode"

        if self.position_tp_mode == "Full Mode" and check_tp_sl != "Full Mode":
            self.session_auth.full_partial_position_tp_sl_switch(
                symbol=self.symbol,
                tp_sl_mode="Full"
            )
        elif self.position_tp_mode == "Partial Mode" and check_tp_sl != "Partial Mode":
            self.session_auth.full_partial_position_tp_sl_switch(
                symbol=self.symbol,
                tp_sl_mode="Partial"
            )

    # установка idx для позиции
    def set_position_idx(self):
        if self.position_mode == "One-Way Mode":
            self.position_idx = 0

        elif self.position_mode == "Hedge Mode":

            if self.order == "Buy":
                self.position_idx = 1

            elif self.order == "Sell":
                self.position_idx = 2

    # получаем данные о балансе и вычисляем объем ордера
    def balance_volume(self):
        wallet_balance = self.session_auth.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
        last_price = self.session_auth.orderbook(symbol=self.symbol)['result'][0]['price']
        order_balance = float(wallet_balance) * (float(self.percent_balance) / 100) * int(self.leverage)
        order_size = float(order_balance) / float(last_price)
        return order_size

    # открытие позиции
    def open_trade(self):
        qty_order = round(self.balance_volume(), int(self.round_volume))
        self.session_auth.place_active_order(
            symbol=self.symbol,
            side=self.order,
            order_type="Market",
            qty=qty_order,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False,
            position_idx=self.position_idx
        )
        if self.multi_take == "false":
            self.tp_sl_profit(qty_order)
        if self.multi_take == "true":
            self.tp_sl_profit_multi(qty_order)

    # установка тейк профита и стоп лосса
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
            position_idx=self.position_idx
        )

    # установка тейк профита и стоп лосса для мультитейка
    def tp_sl_profit_multi(self, qty_order):
        first_take_volume = round(float(qty_order) * (int(self.close_volume_first) / 100), int(self.round_volume))
        second_take_volume = round(float(qty_order) * (int(self.close_volume_second) / 100), int(self.round_volume))
        three_take_volume = round(float(qty_order) - first_take_volume - second_take_volume, int(self.round_volume))

        # первый тейк профит
        self.session_auth.set_trading_stop(
            symbol=self.symbol,
            side=self.order,
            take_profit=float(self.take_profit_price),
            tp_trigger_by="LastPrice",
            tp_size=first_take_volume,
            position_idx=self.position_idx
        )

        # второй тейк профит
        self.session_auth.set_trading_stop(
            symbol=self.symbol,
            side=self.order,
            take_profit=float(self.take_profit_two_price),
            tp_trigger_by="LastPrice",
            tp_size=second_take_volume,
            position_idx=self.position_idx
        )

        # третий тейк профит
        self.session_auth.set_trading_stop(
            symbol=self.symbol,
            side=self.order,
            take_profit=float(self.take_profit_three_price),
            tp_trigger_by="LastPrice",
            tp_size=three_take_volume,
            position_idx=self.position_idx
        )

        # установка стоп лосса
        if self.order == "Sell":
            self.new_order = "Buy"

        if self.order == "Buy":
            self.new_order = "Sell"

        self.session_auth.place_conditional_order(
            symbol=self.symbol,
            order_type="Market",
            side=self.new_order,
            qty=float(qty_order),
            base_price=float(self.base_price),
            stop_px=float(self.stop_loss_price),
            time_in_force="GoodTillCancel",
            trigger_by="LastPrice",
            reduce_only=False,
            close_on_trigger=False,
            position_idx=self.position_idx
        )

    def cancel_sl(self):
        check_size_position = (self.session_auth.my_position(
            symbol=self.symbol
        ))
        if check_size_position["result"][0]["size"] > 0:
            self.session_auth.cancel_all_conditional_orders(
                symbol=self.symbol
            )

    def new_sl(self):
        qty_order = self.session_auth.my_position(symbol=self.symbol)
        self.session_auth.place_conditional_order(
            symbol=self.symbol,
            order_type="Market",
            side=self.new_order,
            qty=float(qty_order["result"][0]["size"]),
            base_price=float(self.base_price_second),
            stop_px=float(self.stop_loss_two_price),
            time_in_force="GoodTillCancel",
            trigger_by="LastPrice",
            reduce_only=False,
            close_on_trigger=False,
            position_idx=self.position_idx
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
