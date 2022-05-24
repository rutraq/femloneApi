import time
import pybit
import openpyxl
from flask import Flask, request
from threading import Thread
import telebot
import re
from datetime import datetime

session = pybit.HTTP("https://api.bybit.com",
                     api_key="TCBkATA9S2SdcigMWG", api_secret="PoGWXQGKZrHQ0sTZh5GtcvfkSPdy76hZM5LH")

app = Flask(__name__)


@app.route("/webHookReceive", methods=["POST"])
def make_order():
    search_symbol = request.data.decode()
    if re.search('^[A-Z]+-(Sell|Buy)$', search_symbol) is not None:
        telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", search_symbol)
        th = Thread(target=ByBit, args=(search_symbol,))
        th.start()
    return "200"


def record_exceptions(err):
    now = datetime.today().strftime("%d-%m-%Y %H:%M")
    telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335",
                                                                                   "Новая ошибка на сервере!")
    with open("errors.txt", 'w+') as file:
        error = "{0}  {1}\n".format(now, err)
        file.write(error)


@app.route("/check", methods=["GET"])
def check():
    return "everything is all right"


class ByBit:
    def __init__(self, search_symbol):
        self.leverage = None
        self.percentage_of_balance = None
        self.take_profit_one = None
        self.closing_volume_one = None
        self.take_profit_two = None
        self.closing_volume_two = None
        self.stop_loss_one = None
        self.stop_loss_two = None
        self.multi_take = None
        self.qty_position_round = None
        self.id_stop_loss_two = None
        self.side = None

        try:
            self.open_excel(search_symbol)
        except Exception as err:
            record_exceptions(err)

    def open_excel(self, search_symbol):
        wb = openpyxl.load_workbook('main.xlsx')
        sheet = wb['Лист1']
        count_row = sheet.max_row
        self.search_excel_info(search_symbol, count_row, sheet)

    def search_excel_info(self, search_symbol, count_row, sheet):
        for i in range(count_row):
            row_excel = sheet[f'A{int(i + 2)}'].value
            if search_symbol.split('-')[0] == row_excel:
                self.leverage = self.values_from_excel(sheet, 'B', i)
                self.percentage_of_balance = self.values_from_excel(sheet, 'C', i)
                self.multi_take = self.values_from_excel(sheet, 'D', i)
                self.take_profit_one = self.values_from_excel(sheet, 'E', i)
                self.closing_volume_one = self.values_from_excel(sheet, 'F', i)
                self.take_profit_two = self.values_from_excel(sheet, 'G', i)
                self.closing_volume_two = self.values_from_excel(sheet, 'H', i)
                self.stop_loss_one = self.values_from_excel(sheet, 'I', i)
                self.stop_loss_two = self.values_from_excel(sheet, 'J', i)
                self.qty_position_round = self.values_from_excel(sheet, 'K', i)
        self.open_trade(search_symbol)

    @staticmethod
    def values_from_excel(sheet, letter, row):
        return sheet[f'{letter}{int(row + 2)}'].value

    def volume_position(self):
        wallet_balance = session.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
        balance_position = wallet_balance * self.percentage_of_balance / 100 * self.leverage
        return balance_position

    def place_order(self, search_symbol):
        if int(session.my_position(symbol=search_symbol.split('-')[0])['result'][0]['size']) == 0:
            price_position = self.volume_position()
            last_price = session.orderbook(symbol=search_symbol.split('-')[0])['result'][0]['price']
            qty_position = round(float(float(price_position) / float(last_price)), self.qty_position_round)
            try:
                round_number = int(len(last_price.split('.')[1]))
            except IndexError:
                round_number = 0
            session.place_active_order(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                order_type="Market",
                qty=qty_position,
                time_in_force="GoodTillCancel",
                reduce_only=False,
                close_on_trigger=False,
                position_idx=0
            )
            return round_number, qty_position

    def place_order_with_stop(self, order_type, search_symbol):
        try:
            round_number, qty_position = self.place_order(search_symbol)

            price_my_position = (session.my_position(symbol=search_symbol.split('-')[0]))
            price = float((price_my_position['result'][0]['entry_price']))
            price = round(price, round_number)
            if order_type == "long":
                stop_loss = price - price * (self.stop_loss_one / 100)
                take_profit = price + price * (self.take_profit_one / 100)
            else:
                stop_loss = price + price * (self.stop_loss_one / 100)
                take_profit = price - price * (self.take_profit_one / 100)

            session.set_trading_stop(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                take_profit=round(take_profit, round_number),
                stop_loss=round(stop_loss, round_number),
                tp_trigger_by="LastPrice",
                sl_trigger_by="LastPrice",
                tp_size=qty_position,
                sl_size=qty_position,
                position_idx=0
            )
            order_name = re.search("^[A-Z]+", search_symbol)
            message = "_Сделка:_ *{0}*\n_Тип:_ {1}\n_Цена:_ {2}\n_Take profit:_ {3}\n_Stop loss:_ {4}".format(
                order_name[0],
                order_type,
                price, take_profit,
                stop_loss)
            telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", message,
                                                                                           parse_mode="Markdown")
        except TypeError:
            # Позиция уже открыта
            pass

    @staticmethod
    def send_order_to_telegram(order_name, multi_type, price, take_profit, take_profit2,
                               stop_loss, stop_loss_2):
        message = "_Сделка:_ *{0}*\n_Тип:_ {1}\n_Цена:_ {2}\n_Take profit 1:_ {3}\n" \
                  "_Take profit 2:_ {4}\n_Stop loss 1:_ {5}\n_Stop loss 2:_ {6}".format(order_name[0],
                                                                                        multi_type,
                                                                                        price,
                                                                                        round(take_profit, 2),
                                                                                        round(take_profit2, 2),
                                                                                        round(stop_loss, 2),
                                                                                        round(stop_loss_2, 2))
        telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", message,
                                                                                       parse_mode="Markdown")

    def short_multi_take(self, search_symbol):
        try:
            round_number, qty_position = self.place_order(search_symbol)
            price = float((session.my_position(symbol=search_symbol.split('-')[0])['result'][0]['entry_price']))
            stop_loss = price + price * (float(self.stop_loss_one) / 100)
            stop_loss = stop_loss - stop_loss * 0.25 / 100
            bs_price = stop_loss * 0.25 / 100 + stop_loss
            stop_loss_2 = price - price * (float(self.stop_loss_two) / 100)
            stop_loss_2 = stop_loss_2 - stop_loss_2 * 0.25 / 100
            bs_price_2 = stop_loss * 0.25 / 100 + stop_loss_2
            take_profit = price - price * (float(self.take_profit_one) / 100)
            take_profit2 = price - price * (float(self.take_profit_two) / 100)
            two_take_profit_qty = self.set_take_profit(qty_position, search_symbol, take_profit, take_profit2,
                                                       round_number)

            if round(bs_price, round_number) > round(stop_loss, round_number):
                try:
                    session.place_conditional_order(
                        symbol=search_symbol.split('-')[0],
                        side="Buy",
                        order_type="Market",
                        trigger_by="LastPrice",
                        qty=qty_position,
                        base_price=round(stop_loss, round_number),
                        stop_px=round(bs_price, round_number),
                        time_in_force="GoodTillCancel",
                        reduce_only=False,
                        position_idx=0
                    )
                except pybit.exceptions.InvalidRequestError:
                    session.place_conditional_order(
                        symbol=search_symbol.split('-')[0],
                        side="Buy",
                        order_type="Market",
                        trigger_by="LastPrice",
                        qty=qty_position,
                        base_price=round(stop_loss, round_number),
                        stop_px=round(bs_price, round_number),
                        time_in_force="GoodTillCancel",
                        reduce_only=False,
                        position_idx=0
                    )

            order_name = re.search("^[A-Z]+", search_symbol)
            self.send_order_to_telegram(order_name, "Short multi take", price, take_profit, take_profit2,
                                        stop_loss, stop_loss_2)

            self.order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty)
        except TypeError:
            # Позиция уже открыта
            pass

    def set_take_profit(self, qty_position, search_symbol, take_profit, take_profit2, round_number):
        try:
            first_take_profit_qty = round(qty_position * self.closing_volume_one / 100, self.qty_position_round)
            two_take_profit_qty = round(qty_position - first_take_profit_qty, self.qty_position_round)
            session.set_trading_stop(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                take_profit=round(take_profit, round_number),
                tp_trigger_by="LastPrice",
                sl_trigger_by="LastPrice",
                tp_size=first_take_profit_qty,
                sl_size=qty_position,
                position_idx=0
            )

            session.set_trading_stop(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                take_profit=round(take_profit2, round_number),
                tp_trigger_by="LastPrice",
                sl_trigger_by="LastPrice",
                tp_size=two_take_profit_qty,
                position_idx=0
            )
            return two_take_profit_qty
        except pybit.exceptions.InvalidRequestError:
            first_take_profit_qty = round(qty_position * self.closing_volume_one / 100, self.qty_position_round)
            two_take_profit_qty = round(qty_position - first_take_profit_qty, self.qty_position_round)
            session.set_trading_stop(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                take_profit=round(take_profit, round_number),
                tp_trigger_by="LastPrice",
                sl_trigger_by="LastPrice",
                tp_size=first_take_profit_qty,
                sl_size=qty_position,
                position_idx=0
            )

            session.set_trading_stop(
                symbol=search_symbol.split('-')[0],
                side=search_symbol.split('-')[1],
                take_profit=round(take_profit2, round_number),
                tp_trigger_by="LastPrice",
                sl_trigger_by="LastPrice",
                tp_size=two_take_profit_qty,
                position_idx=0
            )
            return two_take_profit_qty

    def long_multi_take(self, search_symbol):
        try:
            round_number, qty_position = self.place_order(search_symbol)
            price = float((session.my_position(symbol=search_symbol.split('-')[0])['result'][0]['entry_price']))
            stop_loss = price - price * (float(self.stop_loss_one) / 100)
            stop_loss = stop_loss + stop_loss * 0.25 / 100
            bs_price = stop_loss - stop_loss * 0.25 / 100
            stop_loss_2 = price + price * (float(self.stop_loss_two) / 100)
            stop_loss_2 = stop_loss_2 + stop_loss_2 * 0.25 / 100
            bs_price_2 = stop_loss_2 - stop_loss_2 * 0.25 / 100
            take_profit = price + price * (float(self.take_profit_one) / 100)
            take_profit2 = price + price * (float(self.take_profit_two) / 100)
            two_take_profit_qty = self.set_take_profit(qty_position, search_symbol, take_profit, take_profit2,
                                                       round_number)

            if round(bs_price, round_number) < round(stop_loss, round_number):
                try:
                    session.place_conditional_order(
                        symbol=search_symbol.split('-')[0],
                        side="Sell",
                        order_type="Market",
                        trigger_by="LastPrice",
                        qty=qty_position,
                        base_price=round(stop_loss, round_number),
                        stop_px=round(bs_price, round_number),
                        time_in_force="GoodTillCancel",
                        reduce_only=False,
                        position_idx=0
                    )
                except pybit.exceptions.InvalidRequestError:
                    session.place_conditional_order(
                        symbol=search_symbol.split('-')[0],
                        side="Sell",
                        order_type="Market",
                        trigger_by="LastPrice",
                        qty=qty_position,
                        base_price=round(stop_loss, round_number),
                        stop_px=round(bs_price, round_number),
                        time_in_force="GoodTillCancel",
                        reduce_only=False,
                        position_idx=0
                    )
            order_name = re.search("^[A-Z]+", search_symbol)
            self.send_order_to_telegram(order_name, "Long multi take", price, take_profit, take_profit2,
                                        stop_loss, stop_loss_2)

            self.order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty)
        except TypeError:
            # Позиция уже открыта
            pass

    @staticmethod
    def order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty):
        side = ""
        id_stop_loss_two = ""
        a = 1
        global k
        k = 1
        test = []
        first_take_close = False
        while a == 1:
            information_order = session.get_conditional_order(symbol=search_symbol.split('-')[0])['result']['data']
            for i in information_order:
                if i['order_status'] == "Untriggered":
                    test.append(i)
                if len(test) == 3:
                    a = 0
            time.sleep(1.5)
        id_first_take_profit = test[2]['stop_order_id']
        id_two_take_profit = test[1]['stop_order_id']
        id_stop_loss = test[0]['stop_order_id']
        while k == 1:
            information_order = session.get_conditional_order(symbol=search_symbol.split('-')[0])['result']['data']
            for i in information_order:
                if i['stop_order_id'] == id_first_take_profit and i['order_status'] == "Filled" \
                        and first_take_close == False and i['stop_order_id'] != "" and id_first_take_profit != "":
                    # закрыли первый тейк
                    try:
                        session.cancel_conditional_order(symbol=search_symbol.split('-')[0], stop_order_id=id_stop_loss)
                    except:
                        session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])

                    try:
                        if search_symbol.split('-')[1] == "Buy":
                            side = 'Sell'
                        if search_symbol.split('-')[1] == "Sell":
                            side = 'Buy'
                        id_stop_loss_two = session.place_conditional_order(
                            symbol=search_symbol.split('-')[0],
                            side=side,
                            order_type="Market",
                            trigger_by="LastPrice",
                            qty=two_take_profit_qty,
                            base_price=round(stop_loss_2, round_number),
                            stop_px=round(bs_price_2, round_number),
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            position_idx=0)['result']['stop_order_id']
                        telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y") \
                            .send_message("-699678335", "Закрылся первый take profit по паре: {0}, по цене: {1}\n"
                                                        "Открылся новый stop loss по цене: {2}"
                                          .format(search_symbol, i['trigger_price'],
                                                  round(stop_loss_2, round_number)))
                    except pybit.exceptions.InvalidRequestError:
                        # цена второго стопа выше чем цена
                        session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                        session.place_active_order(
                            symbol=search_symbol.split('-')[0],
                            side=side,
                            order_type="Market",
                            qty=two_take_profit_qty,
                            time_in_force="GoodTillCancel",
                            reduce_only=False,
                            close_on_trigger=False,
                            position_idx=0
                        )
                        k = 0
                        id_first_take_profit = ""
                        id_two_take_profit = ""
                        id_stop_loss = ""

                    first_take_close = True
                if i['stop_order_id'] == id_two_take_profit and i['order_status'] == "Filled" \
                        and i['stop_order_id'] != "" and id_two_take_profit != "":
                    # закрыли второй тейк
                    session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                    first_take_close = False
                    id_first_take_profit = ""
                    id_two_take_profit = ""
                    id_stop_loss = ""
                    k = 0
                if i['stop_order_id'] == id_stop_loss_two and i['order_status'] == "Filled" \
                        and i['stop_order_id'] != "" and id_stop_loss_two != "":
                    session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                    # закрыли второй стоп
                    first_take_close = False
                    id_first_take_profit = ""
                    id_two_take_profit = ""
                    id_stop_loss = ""
                    k = 0
                if i['stop_order_id'] == id_stop_loss and i['order_status'] == "Filled" \
                        and i['stop_order_id'] != "" and id_stop_loss != "":
                    # вылетели по первому стопу
                    telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y") \
                        .send_message("-699678335", "Закрылся по stop loss по паре: {0}".format(search_symbol))
                    session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                    first_take_close = False
                    id_first_take_profit = ""
                    id_two_take_profit = ""
                    id_stop_loss = ""
                    k = 0
            time.sleep(2)

    def open_trade(self, search_symbol):
        if search_symbol.split('-')[1] == "Buy" and self.multi_take == "false":
            self.place_order_with_stop("long", search_symbol)
        if search_symbol.split('-')[1] == "Sell" and self.multi_take == "false":
            self.place_order_with_stop("short", search_symbol)
        if search_symbol.split('-')[1] == "Buy" and self.multi_take == "true":
            self.long_multi_take(search_symbol)
        if search_symbol.split('-')[1] == "Sell" and self.multi_take == "true":
            self.short_multi_take(search_symbol)


if __name__ == "__main__":
    app.run()
