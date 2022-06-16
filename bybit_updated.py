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
    telebot.TeleBot("5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y").send_message("-699678335", strings)
    th = Thread(target=ByBit, args=(strings,))
    try:
        th.start()
    except Exception as err:
        record_exceptions(err)
    return "200"


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


class ByBit:
    def __init__(self, strings):
        self.check = strings.split("&&")
        self.main_information = []
        self.round_price = {"BTCUSDT": 1, "ETHUSDT": 2, "SOLUSDT": 3}
        self.round_volume = {"BTCUSDT": 3, "ETHUSDT": 2, "SOLUSDT": 1}
        self.balance_position = None
        for i in check:
            k = i.split(":")[1]
            self.main_information.append(k)
        self.session_auth = usdt_perpetual.HTTP(
            endpoint="https://api-testnet.bybit.com",
            api_key="FR2Kub0qvCv3WjoERa",
            api_secret="hn9zNpEuxrFY5SVlqMAEd3h3ZmWzPtpgcpFA"
        )
        self.volume_position()

    def volume_position(self):
        if self.main_information[0] == "false":
            leverage = self.main_information[6]
            percent_balance = self.main_information[7]
        else:
            leverage = self.main_information[10]
            percent_balance = self.main_information[11]

        wallet_balance = self.session_auth.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
        last_price = self.session_auth.orderbook(symbol=self.main_information[1])['result'][0]['price']
        self.balance_position = round(wallet_balance * percent_balance / 100 * float(leverage) / float(last_price),
                                      int(self.round_volume.get(self.main_information[1])))
        self.place_active_order()

    def place_active_order(self):
        self.session_auth.place_active_order(
            symbol=self.main_information[1],
            side=self.main_information[2],
            order_type="Market",
            qty=self.balance_position,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            close_on_trigger=False,
            position_idx=0
        )
        if self.main_information[0] == "false":
            self.set_trading_stop()
        else:
            self.set_trading_stop_multi()

    def set_trading_stop(self):
        self.session_auth.set_trading_stop(
            symbol=self.main_information[1],
            side=self.main_information[2],
            take_profit=self.main_information[4].replace(",", ""),
            stop_loss=self.main_information[5].replace(",", ""),
            tp_trigger_by="LastPrice",
            sl_trigger_by="LastPrice",
            tp_size=self.balance_position,
            sl_size=self.balance_position,
            position_idx=0
        )

    def set_trading_stop_multi(self):
        first_take = round(float(self.balance_position) * (float(self.main_information[8]) / 100),
                           int(self.round_volume.get(self.main_information[1])))
        two_take = float(self.balance_position) - first_take
        # первый тейк
        first_take_id = self.session_auth.set_trading_stop(
            symbol=self.main_information[1],
            side=self.main_information[2],
            take_profit=self.main_information[4].replace(",", ""),
            tp_trigger_by="LastPrice",
            tp_size=first_take,
            position_idx=0
        )
        # Второй тейк
        self.session_auth.set_trading_stop(
            symbol=self.main_information[1],
            side=self.main_information[2],
            take_profit=self.main_information[6].replace(",", ""),
            tp_trigger_by="LastPrice",
            tp_size=two_take,
            position_idx=0
        )

        # Стоп лосс
        if self.main_information[2] == "Buy":
            order_side = "Sell"
            stop_px_price = abs(round(float(self.main_information[5].replace(",", "")) * (0.1 + 100) / 100,
                                      int(self.round_price.get(self.main_information[1]))))
            base_price = abs(round(float(self.main_information[5].replace(",", "")) * (0.2 + 100) / 100,
                                   int(self.round_price.get(self.main_information[1]))))
            price = float(self.main_information[5].replace(",", ""))
        else:
            order_side = "Buy"
            stop_px_price = abs(round(float(self.main_information[5].replace(",", "")) * (0.1 - 100) / 100,
                                      int(self.round_price.get(self.main_information[1]))))
            base_price = abs(round(float(self.main_information[5].replace(",", "")) * (0.2 - 100) / 100,
                                   int(self.round_price.get(self.main_information[1]))))
            price = float(self.main_information[5].replace(",", ""))

        self.session_auth.place_conditional_order(
            symbol=self.main_information[1],
            side=order_side,
            order_type="Limit",
            trigger_by="LastPrice",
            qty=self.balance_position,
            base_price=base_price,
            stop_px=stop_px_price,
            price=price,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            position_idx=0
        )
        self.order_tracking()

    def open_second_stop_loss(self):
        if self.main_information[2] == "Buy":
            order_side = "Sell"
            stop_px_price = abs(round(float(self.main_information[7].replace(",", "")) * (0.1 + 100) / 100,
                                      int(self.round_price.get(self.main_information[1]))))
            base_price = abs(round(float(self.main_information[7].replace(",", "")) * (0.2 + 100) / 100,
                                   int(self.round_price.get(self.main_information[1]))))
            price = float(self.main_information[7].replace(",", ""))
        else:
            order_side = "Buy"
            stop_px_price = abs(round(float(self.main_information[7].replace(",", "")) * (0.1 - 100) / 100,
                                      int(self.round_price.get(self.main_information[1]))))
            base_price = abs(round(float(self.main_information[7].replace(",", "")) * (0.2 - 100) / 100,
                                   int(self.round_price.get(self.main_information[1]))))
            price = float(self.main_information[7].replace(",", ""))

        second_stop_id = self.session_auth.place_conditional_order(
            symbol=self.main_information[1],
            side=order_side,
            order_type="Limit",
            trigger_by="LastPrice",
            qty=self.balance_position,
            base_price=base_price,
            stop_px=stop_px_price,
            price=price,
            time_in_force="GoodTillCancel",
            reduce_only=False,
            position_idx=0
        )
        return second_stop_id

    @staticmethod
    def get_name(dictionary):
        return dictionary['trigger_price']

    def order_tracking(self):
        close_position = False
        check_order = False

        check_first_take_id = False

        first_take_id = ""
        second_take_id = ""
        first_stop_id = ""
        second_stop_id = ""
        order_information_id = []

        while not check_order:
            information_order = self.session_auth.get_conditional_order(symbol=self.main_information[1])['result'][
                'data']
            for k in information_order:
                if k['order_status'] == "Untriggered":
                    order_information_id.append(k)
                    if len(order_information_id) == 2:
                        check_order = True
            time.sleep(3)
        order_information_id.sort(key=self.get_name)

        for k in order_information_id:
            print(k)

        if self.main_information[2] == "Sell":
            first_stop_id = order_information_id[2]['stop_order_id']
            first_take_id = order_information_id[1]['stop_order_id']
            second_take_id = order_information_id[0]['stop_order_id']
        if self.main_information[2] == "Buy":
            first_stop_id = order_information_id[0]['stop_order_id']
            first_take_id = order_information_id[1]['stop_order_id']
            second_take_id = order_information_id[2]['stop_order_id']

        while not close_position:
            information_order = self.session_auth.get_conditional_order(symbol=self.main_information[1])['result'][
                'data']
            for k in information_order:

                # Улетели по стоп лоссу
                if k['order_status'] == "Filled" and first_stop_id == k['stop_order_id']:
                    close_position = True

                # Закрыли первый тейк отменили первый стоп и открыли второй стоп
                if k['order_status'] == "Filled" and first_take_id == k['stop_order_id'] and not check_first_take_id:
                    self.session_auth.cancel_conditional_order(symbol=self.main_information[1],
                                                               stop_order_id=first_stop_id)
                    second_stop_id = self.open_second_stop_loss()['result'][
                        'stop_order_id']
                    check_first_take_id = True

                # Закрыли второй тейк отменили второй стоп
                if k['order_status'] == "Filled" and second_take_id == k['stop_order_id'] and check_first_take_id:
                    self.session_auth.cancel_conditional_order(symbol=self.main_information[1],
                                                               stop_order_id=second_stop_id)
                    close_position = True

                # Улетели по второму стоп лоссу
                if k['order_status'] == "Filled" and second_stop_id == k['stop_order_id'] and check_first_take_id:
                    close_position = True

        print(f"Первый тейк {first_take_id}")
        print(f"Второй тейк {second_take_id}")
        print(f"Стоп лосс {first_stop_id}")


if __name__ == "__main__":
    app.run()
