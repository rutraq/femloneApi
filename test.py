import time
from pybit import usdt_perpetual

# strings = "Multi Take:false&&Symbol:BTCUSDT&&Order:Sell&&Entry Price:25,239&&Take Profit Price:26,390.19&&" \
#           " Loss Price:34,087.80&&Leverage:1"

strings = "Multi Take:true&&" \
          "Symbol:BTCUSDT&&" \
          "Order:Buy&&" \
          "Entry Price:29,735&&" \
          "Take Profit Price:28,000&&" \
          "Stop Loss Price:26,600&&" \
          "Take Profit Two Price:29,000&&" \
          "Stop Loss Two Price:27,600&&" \
          "Close Volume First:50&&" \
          "Close Volume Second:50&&" \
          "Leverage:1"

check = strings.split("&&")
main_information = []

round_price = {"BTCUSDT": 1, "ETHUSDT": 2, "NEARUSDT": 3}
round_volume = {"BTCUSDT": 3, "ETHUSDT": 2, "NEARUSDT": 1}

for i in check:
    k = i.split(":")[1]
    main_information.append(k)

session_auth = usdt_perpetual.HTTP(
    endpoint="https://api-testnet.bybit.com",
    api_key="L0eMYzbfFHRJywa9wk",
    api_secret="tjmyrZHOkyGnvAtLxW7gS26wc2xGngcmoZfT"
)


def volume_position():
    if main_information[0] == "false":
        leverage = main_information[6]
    else:
        leverage = main_information[10]
    wallet_balance = session_auth.get_wallet_balance(coin="USDT")['result']['USDT']['equity']
    last_price = session_auth.orderbook(symbol=main_information[1])['result'][0]['price']
    balance_position = round(wallet_balance * 2.5 / 100 * float(leverage) / float(last_price), int(round_volume.get(main_information[1])))
    place_active_order(main_information, balance_position)


def place_active_order(main_information, balance_position):
    session_auth.place_active_order(
        symbol=main_information[1],
        side=main_information[2],
        order_type="Market",
        qty=balance_position,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        close_on_trigger=False,
        position_idx=0
    )
    if main_information[0] == "false":
        set_trading_stop(main_information, balance_position)
    else:
        set_trading_stop_multi(main_information, balance_position)


def set_trading_stop(main_information, balance_position):
    session_auth.set_trading_stop(
        symbol=main_information[1],
        side=main_information[2],
        take_profit=main_information[4].replace(",", ""),
        stop_loss=main_information[5].replace(",", ""),
        tp_trigger_by="LastPrice",
        sl_trigger_by="LastPrice",
        tp_size=balance_position,
        sl_size=balance_position,
        position_idx=0
    )


def set_trading_stop_multi(main_information, balance_position):
    first_take = round(float(balance_position) * (float(main_information[8]) / 100), int(round_volume.get(main_information[1])))
    two_take = float(balance_position) - first_take
    # первый тейк
    first_take_id = session_auth.set_trading_stop(
        symbol=main_information[1],
        side=main_information[2],
        take_profit=main_information[4].replace(",", ""),
        tp_trigger_by="LastPrice",
        tp_size=first_take,
        position_idx=0
    )
    # Второй тейк
    session_auth.set_trading_stop(
        symbol=main_information[1],
        side=main_information[2],
        take_profit=main_information[6].replace(",", ""),
        tp_trigger_by="LastPrice",
        tp_size=two_take,
        position_idx=0
    )

    # Стоп лосс
    if main_information[2] == "Buy":
        order_side = "Sell"
        stop_px_price = abs(round(float(main_information[5].replace(",", "")) * (0.1 + 100) / 100, int(round_price.get(main_information[1]))))
        base_price = abs(round(float(main_information[5].replace(",", "")) * (0.2 + 100) / 100, int(round_price.get(main_information[1]))))
        price = float(main_information[5].replace(",", ""))
    else:
        order_side = "Buy"
        stop_px_price = abs(round(float(main_information[5].replace(",", "")) * (0.1 - 100) / 100, int(round_price.get(main_information[1]))))
        base_price = abs(round(float(main_information[5].replace(",", "")) * (0.2 - 100) / 100, int(round_price.get(main_information[1]))))
        price = float(main_information[5].replace(",", ""))

    session_auth.place_conditional_order(
        symbol=main_information[1],
        side=order_side,
        order_type="Limit",
        trigger_by="LastPrice",
        qty=balance_position,
        base_price=base_price,
        stop_px=stop_px_price,
        price=price,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        position_idx=0
    )
    order_tracking(main_information, two_take)


def open_second_stop_loss(main_information, balance_position):

    if main_information[2] == "Buy":
        order_side = "Sell"
        stop_px_price = abs(round(float(main_information[7].replace(",", "")) * (0.1 + 100) / 100, int(round_price.get(main_information[1]))))
        base_price = abs(round(float(main_information[7].replace(",", "")) * (0.2 + 100) / 100, int(round_price.get(main_information[1]))))
        price = float(main_information[7].replace(",", ""))
    else:
        order_side = "Buy"
        stop_px_price = abs(round(float(main_information[7].replace(",", "")) * (0.1 - 100) / 100, int(round_price.get(main_information[1]))))
        base_price = abs(round(float(main_information[7].replace(",", "")) * (0.2 - 100) / 100, int(round_price.get(main_information[1]))))
        price = float(main_information[7].replace(",", ""))

    second_stop_id = session_auth.place_conditional_order(
        symbol=main_information[1],
        side=order_side,
        order_type="Limit",
        trigger_by="LastPrice",
        qty=balance_position,
        base_price=base_price,
        stop_px=stop_px_price,
        price=price,
        time_in_force="GoodTillCancel",
        reduce_only=False,
        position_idx=0
    )
    return second_stop_id



def get_name(dictionary):
    return dictionary['trigger_price']


def order_tracking(main_information, balance_position_two_stop):
    close_position = False
    check_order = False

    check_first_take_id = False

    first_take_id = ""
    second_take_id = ""
    first_stop_id = ""
    second_stop_id = ""
    order_information_id = []

    while not check_order:
        information_order = session_auth.get_conditional_order(symbol=main_information[1])['result']['data']
        for k in information_order:
            if k['order_status'] == "Untriggered":
                order_information_id.append(k)
                if len(order_information_id) == 2:
                    check_order = True
        time.sleep(3)
    order_information_id.sort(key=get_name)

    for k in order_information_id:
        print(k)

    if main_information[2] == "Sell":
        first_stop_id = order_information_id[2]['stop_order_id']
        first_take_id = order_information_id[1]['stop_order_id']
        second_take_id = order_information_id[0]['stop_order_id']
    if main_information[2] == "Buy":
        first_stop_id = order_information_id[0]['stop_order_id']
        first_take_id = order_information_id[1]['stop_order_id']
        second_take_id = order_information_id[2]['stop_order_id']

    while not close_position:
        information_order = session_auth.get_conditional_order(symbol=main_information[1])['result']['data']
        for k in information_order:

            # Улетели по стоп лоссу
            if k['order_status'] == "Filled" and first_stop_id == k['stop_order_id']:
                close_position = True

            # Закрыли первый тейк отменили первый стоп и открыли второй стоп
            if k['order_status'] == "Filled" and first_take_id == k['stop_order_id'] and not check_first_take_id:
                session_auth.cancel_conditional_order(symbol=main_information[1], stop_order_id=first_stop_id)
                second_stop_id = open_second_stop_loss(main_information, balance_position_two_stop)['result']['stop_order_id']
                check_first_take_id = True

            # Закрыли второй тейк отменили второй стоп
            if k['order_status'] == "Filled" and second_take_id == k['stop_order_id'] and check_first_take_id:
                session_auth.cancel_conditional_order(symbol=main_information[1], stop_order_id=second_stop_id)
                close_position = True

            # Улетели по второму стоп лоссу
            if k['order_status'] == "Filled" and second_stop_id == k['stop_order_id'] and check_first_take_id:
                close_position = True

    print(f"Первый тейк {first_take_id}")
    print(f"Второй тейк {second_take_id}")
    print(f"Стоп лосс {first_stop_id}")


volume_position()
