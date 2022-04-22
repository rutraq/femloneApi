import telebot
from telebot import types
import pybit


class TelegramBot:
    def __init__(self):
        self.token = "5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y"
        self.bot = telebot.TeleBot(self.token)
        self.group_id = "-699678335"
        self.session = pybit.HTTP("https://api-testnet.bybit.com",
                                  api_key="XiDGurqyUmnY0Qjh4a", api_secret="NbXvPCNNMmCCpfrmIQIVeNeSly8fBb9MPviA")

        markup = types.ReplyKeyboardMarkup(row_width=2)
        command1 = types.KeyboardButton('Баланс')
        command2 = types.KeyboardButton('Пидор ли женя?')
        command3 = types.KeyboardButton('Открытые позиции')
        markup.add(command1, command2, command3)
        self.bot.send_message(self.group_id, "Выберите команду:", reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            if message.text == "Пидор ли женя?":
                self.bot.send_message(self.group_id, "Конечно да!")
            elif message.text == "Открытые позиции":
                self.get_positions()
            elif message.text == "Баланс":
                self.get_balance()

        self.bot.polling(none_stop=True, interval=0)

    def get_balance(self):
        balance = round(self.session.get_wallet_balance(coin="USDT")['result']['USDT']['equity'], 2)
        self.bot.send_message(self.group_id, "Ваш баланс USDT: {0}".format(balance))

    def get_positions(self):
        positions = ""
        for position in self.session.my_position(symbol="BTCUSDT")['result']:
            positions += position['symbol'] + ", "
        self.bot.send_message(self.group_id, positions)


if __name__ == "__main__":
    TelegramBot()
