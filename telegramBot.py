import openpyxl
import telebot
from telebot import types
import pybit
import os


class TelegramBot:
    def __init__(self):
        self.token = "5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y"
        self.bot = telebot.TeleBot(self.token)
        self.group_id = "-699678335"
        self.session = pybit.HTTP("https://api.bybit.com",
                                  api_key="oMF5d6V3kf4DQOcX20", api_secret="Zv9FrzWpKk39CSUMVmZlGDqkEHfAE1HboLmz")

        markup = types.ReplyKeyboardMarkup(row_width=2)
        command1 = types.KeyboardButton('Баланс')
        command2 = types.KeyboardButton('Пидор ли женя?')
        command3 = types.KeyboardButton('Открытые позиции')
        command4 = types.KeyboardButton('Ошибки')
        command5 = types.KeyboardButton('Какая-то пупа залупа')
        markup.add(command1, command2, command3, command4, command5)
        self.bot.send_message(self.group_id, "Выберите команду:", reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def get_text_messages(message):
            if message.text == "Пидор ли женя?":
                self.bot.send_message(self.group_id, "Конечно да!")
            elif message.text == "Открытые позиции":
                self.get_positions()
            elif message.text == "Баланс":
                self.get_balance()
            elif message.text == "Ошибки":
                self.get_errors()
            elif message.text == "Какая-то пупа залупа":
                self.unrealised_pnl()

        self.bot.infinity_polling()

    def get_balance(self):
        balance = round(self.session.get_wallet_balance(coin="USDT")['result']['USDT']['equity'], 2)
        self.bot.send_message(self.group_id, "Ваш баланс USDT: {0}".format(balance))

    def get_positions(self):
        wb = openpyxl.load_workbook('main.xlsx')
        sheet = wb['Лист1']
        count_row = sheet.max_row
        self.bot.send_message(self.group_id, self.search_excel_info(count_row, sheet))

    def search_excel_info(self, count_row, sheet):
        positions = ""
        for i in range(count_row - 1):
            row_excel = sheet[f'A{int(i + 2)}'].value
            position = self.session.my_position(symbol=row_excel)['result'][0]['position_value']
            if position != 0:
                positions += row_excel + "\n"
        if positions == "":
            positions = "Нет открытых позиций"
        return positions

    def get_errors(self):
        if os.path.isfile("errors.txt"):
            if os.path.getsize("errors.txt") != 0:
                with open("errors.txt", 'rb') as file:
                    self.bot.send_document(self.group_id, file)
            else:
                self.bot.send_message(self.group_id, "Ошибок нет")
        else:
            self.bot.send_message(self.group_id, "Ошибок нет")


    def unrealised_pnl(self):
        balance = round(self.session.get_wallet_balance(coin="USDT")['result']['USDT']['unrealised_pnl'], 2)
        self.bot.send_message(self.group_id, "Ваш unrealised pnl USDT: {0}".format(balance))


if __name__ == "__main__":
    TelegramBot()
