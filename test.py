import time
import pybit
import openpyxl
from flask import Flask, request
from threading import Thread
import telebot

session = pybit.HTTP("https://api-testnet.bybit.com",
                     api_key="XiDGurqyUmnY0Qjh4a", api_secret="NbXvPCNNMmCCpfrmIQIVeNeSly8fBb9MPviA")

app = Flask(__name__)


@app.route("/webHookReceive", methods=["POST"])
def make_order():
    search_symbol = request.data.decode()
    telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", search_symbol)
    th = Thread(target=open_excel, args=(search_symbol,))
    th.start()
    return "200"


@app.route("/check", methods=["GET"])
def check():
    return "everything is all right"


def open_excel(search_symbol):
    wb = openpyxl.load_workbook('main.xlsx')
    sheet = wb['Лист1']
    count_row = sheet.max_row
    search_excel_info(search_symbol, count_row, sheet)


def search_excel_info(search_symbol, count_row, sheet):
    global leverage, percentage_of_balance, take_profit_one, closing_volume_one, take_profit_two, closing_volume_two, stop_loss_one, stop_loss_two, multitake, qty_position_round
    for i in range(count_row):
        row_excel = sheet[f'A{int(i + 2)}'].value
        if search_symbol.split('-')[0] == row_excel:
            leverage = sheet[f'B{int(i + 2)}'].value
            percentage_of_balance = sheet[f'C{int(i + 2)}'].value
            multitake = sheet[f'D{int(i + 2)}'].value
            take_profit_one = sheet[f'E{int(i + 2)}'].value
            closing_volume_one = sheet[f'F{int(i + 2)}'].value
            take_profit_two = sheet[f'G{int(i + 2)}'].value
            closing_volume_two = sheet[f'H{int(i + 2)}'].value
            stop_loss_one = sheet[f'I{int(i + 2)}'].value
            stop_loss_two = sheet[f'J{int(i + 2)}'].value
            qty_position_round = sheet[f'K{int(i + 2)}'].value
    open_trade(search_symbol, leverage, percentage_of_balance, multitake, take_profit_one, closing_volume_one, take_profit_two, closing_volume_two, stop_loss_one, stop_loss_two, qty_position_round)


def volume_position(leverage, percentage_of_balance):
    wallet_balance = session.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
    balance_position = wallet_balance * percentage_of_balance / 100 * leverage
    return balance_position


def long(search_symbol, take_profit_one, stop_loss_one, leverage, percentage_of_balance, qty_position_round):
    price_position = volume_position(leverage, percentage_of_balance)
    last_price = session.orderbook(symbol=search_symbol.split('-')[0])['result'][0]['price']
    qty_position = round(float(float(price_position) / float(last_price)), qty_position_round)
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
    price_my_position = (session.my_position(symbol=search_symbol.split('-')[0]))
    price = float((price_my_position['result'][0]['entry_price']))
    price = round(price, round_number)
    stop_loss = price - price * (stop_loss_one / 100)
    take_profit = price + price * (take_profit_one / 100)

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


def short(search_symbol, take_profit_one, stop_loss_one, leverage, percentage_of_balance, qty_position_round):
    price_position = volume_position(leverage, percentage_of_balance)
    last_price = session.orderbook(symbol=search_symbol.split('-')[0])['result'][0]['price']
    qty_position = round(float(float(price_position) / float(last_price)), qty_position_round)
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
    price_my_position = (session.my_position(symbol=search_symbol.split('-')[0]))
    price = float((price_my_position['result'][0]['entry_price']))
    price = round(price, round_number)
    stop_loss = price + price * (stop_loss_one / 100)
    take_profit = price - price * (take_profit_one / 100)

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


def short_multi_take(search_symbol, take_profit_one, take_profit_two, stop_loss_one, closing_volume_one, stop_loss_two, leverage, percentage_of_balance, qty_position_round):
    price_position = volume_position(leverage, percentage_of_balance)
    last_price = session.orderbook(symbol=search_symbol.split('-')[0])['result'][0]['price']
    qty_position = round(float(float(price_position) / float(last_price)), qty_position_round)
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
    price = float((session.my_position(symbol=search_symbol.split('-')[0])['result'][0]['entry_price']))
    stop_loss = price + price * (float(stop_loss_one) / 100)
    stop_loss = stop_loss - stop_loss * 0.1 / 100
    bs_price = stop_loss * 0.1 / 100 + stop_loss

    stop_loss_2 = price - price * (float(stop_loss_two) / 100)
    stop_loss_2 = stop_loss_2 - stop_loss_2 * 0.1 / 100
    bs_price_2 = stop_loss * 0.1 / 100 + stop_loss_2

    take_profit = price - price * (float(take_profit_one) / 100)
    take_profit2 = price - price * (float(take_profit_two) / 100)

    first_take_profit_qty = round(qty_position * closing_volume_one / 100, qty_position_round)
    two_take_profit_qty = round(qty_position - first_take_profit_qty, qty_position_round)

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
    order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty)


def long_multi_take(search_symbol, take_profit_one, take_profit_two, stop_loss_one, closing_volume_one, stop_loss_two, leverage, percentage_of_balance, qty_position_round):
    price_position = volume_position(leverage, percentage_of_balance)
    last_price = session.orderbook(symbol=search_symbol.split('-')[0])['result'][0]['price']
    qty_position = round(float(float(price_position) / float(last_price)), qty_position_round)
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
    price = float((session.my_position(symbol=search_symbol.split('-')[0])['result'][0]['entry_price']))
    stop_loss = price - price * (float(stop_loss_one) / 100)
    stop_loss = stop_loss + stop_loss * 0.1 / 100
    bs_price = stop_loss - stop_loss * 0.1 / 100

    stop_loss_2 = price + price * (float(stop_loss_two) / 100)
    stop_loss_2 = stop_loss_2 + stop_loss_2 * 0.1 / 100
    bs_price_2 = stop_loss_2 - stop_loss_2 * 0.1 / 100

    take_profit = price + price * (float(take_profit_one) / 100)
    take_profit2 = price + price * (float(take_profit_two) / 100)

    first_take_profit_qty = round(qty_position * closing_volume_one / 100, qty_position_round)
    two_take_profit_qty = round(qty_position - first_take_profit_qty, qty_position_round)

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
    order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty)


def order_tracking(search_symbol, stop_loss_2, bs_price_2, round_number, two_take_profit_qty):
    global id_stop_loss_two, side
    id_stop_loss_two = ""
    a = 1
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
        time.sleep(4)
    id_first_take_profit = test[2]['stop_order_id']
    id_two_take_profit = test[1]['stop_order_id']
    id_stop_loss = test[0]['stop_order_id']
    while k == 1:
        information_order = session.get_conditional_order(symbol=search_symbol.split('-')[0])['result']['data']
        for i in information_order:
            if i['stop_order_id'] == id_first_take_profit and i['order_status'] == "Filled" and first_take_close == False:
                session.cancel_conditional_order(symbol=search_symbol.split('-')[0], stop_order_id=id_stop_loss)
                if search_symbol.split('-')[1] == "Buy":
                    side = 'Sell'
                if search_symbol.split('-')[1] == "Sell":
                    side = 'Buy'
                    try:
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
                        print(id_stop_loss_two)
                    except pybit.exceptions.InvalidRequestError:
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
                first_take_close = True
            if i['stop_order_id'] == id_two_take_profit and i['order_status'] == "Filled":
                session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                k = 0
            if i['stop_order_id'] == id_stop_loss_two and i['order_status'] == "Filled":
                session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                k = 0
            if i['stop_order_id'] == id_stop_loss and i['order_status'] == "Filled":
                print("Закрылись по стоп лоссу")
                session.cancel_all_conditional_orders(symbol=search_symbol.split('-')[0])
                k = 0
        time.sleep(4)


def open_trade(search_symbol, leverage, percentage_of_balance, multitake, take_profit_one, closing_volume_one, take_profit_two, closing_volume_two, stop_loss_one, stop_loss_two, qty_position_round):
    if search_symbol.split('-')[1] == "Buy" and multitake == "false":
        long(search_symbol, take_profit_one, stop_loss_one, leverage, percentage_of_balance, qty_position_round)
    if search_symbol.split('-')[1] == "Sell" and multitake == "false":
        short(search_symbol, take_profit_one, stop_loss_one, leverage, percentage_of_balance, qty_position_round)
    if search_symbol.split('-')[1] == "Buy" and multitake == "true":
        long_multi_take(search_symbol, take_profit_one, take_profit_two, stop_loss_one, closing_volume_one, stop_loss_two, leverage, percentage_of_balance, qty_position_round)
    if search_symbol.split('-')[1] == "Sell" and multitake == "true":
        short_multi_take(search_symbol, take_profit_one, take_profit_two, stop_loss_one, closing_volume_one, stop_loss_two, leverage, percentage_of_balance, qty_position_round)


if __name__ == "__main__":
    app.run()
