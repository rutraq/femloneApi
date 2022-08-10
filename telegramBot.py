import openpyxl
import telebot
from telebot import types
import pybit
from pybit import exceptions, HTTP
import os
from datetime import datetime
import psycopg2
import cryptocode


class TelegramBot:
    def __init__(self):
        self.token = "5392822083:AAHSdKNl_C60QjyVn0vqYv6jIln6rV2MG9Y"
        self.bot = telebot.TeleBot(self.token)
        self.group_id = "-699678335"
        self.session = HTTP("https://api.bybit.com", api_key="oMF5d6V3kf4DQOcX20",
                            api_secret="Zv9FrzWpKk39CSUMVmZlGDqkEHfAE1HboLmz")
        self.conn = psycopg2.connect(
            "dbname='slihduor' user='slihduor' host='rajje.db.elephantsql.com' password='Z3kDd9k-Hzri0TsNeXOEKYkb7jo9wClC'")
        self.cursor = self.conn.cursor()
        self.last_inline = {}

        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(message.chat.id, "Введите код который вам был выдан.")
            self.bot.register_next_step_handler_by_chat_id(message.chat.id, self.registration)

        @self.bot.message_handler(commands=['commands'])
        def send_commands(message):
            self.send_reply_markup(message.chat.id)

        @self.bot.message_handler(commands=['api_keys'])
        def start_updating_keys(message):
            self.bot.send_message(message.chat.id, "Введите ваш Api key")
            self.bot.register_next_step_handler_by_chat_id(message.chat.id, self.set_api_key)

        # @self.bot.message_handler(content_types=['text'])
        # def get_text_messages(message):
        # if message.text == "Пидор ли женя?":
        #     if self.check_user(message.chat.id):
        #         self.bot.send_message(message.chat.id, "Конечно да!")
        # elif message.text == "Открытые позиции":
        #     if self.check_user(message.chat.id):
        #         self.get_positions()
        # elif message.text == "Баланс":
        #     if self.check_user(message.chat.id):
        #         self.get_balance()
        # elif message.text == "Ошибки":
        #     if self.check_user(message.chat.id):
        #         self.get_errors()
        # elif message.text == "Unrealised pnl":
        #     if self.check_user(message.chat.id):
        #         self.unrealised_pnl()
        # elif message.text == "Дата окончания подписки":
        #     if self.check_user(message.chat.id):
        #         self.check_date_of_subscription(message.chat.id)
        # else:

        @self.bot.callback_query_handler(func=lambda call: True)
        def call_back_handler(message):
            user_id = message.message.chat.id
            if message.data == "pidor":
                if self.check_user(user_id):
                    self.bot.send_message(user_id, "Конечно да!")
                    self.del_and_send_reply(user_id)
            elif message.data == "positions":
                if self.check_user(user_id) and self.check_user_in_keys(user_id):
                    self.get_positions(user_id)
                    self.del_and_send_reply(user_id)
            elif message.data == "balance":
                if self.check_user(user_id) and self.check_user_in_keys(user_id):
                    self.get_balance(user_id)
                    self.del_and_send_reply(user_id)
            elif message.data == "errors":
                if self.check_user(user_id):
                    self.get_errors()
                    self.del_and_send_reply(user_id)
            elif message.data == "pnl":
                if self.check_user(user_id) and self.check_user_in_keys(user_id):
                    self.unrealised_pnl(user_id)
                    self.del_and_send_reply(user_id)
            elif message.data == "date":
                if self.check_user(user_id):
                    self.check_date_of_subscription(user_id)
                    self.del_and_send_reply(user_id)
            self.bot.answer_callback_query(message.id, "")

        self.bot.infinity_polling()

    def del_and_send_reply(self, user_id):
        try:
            self.bot.delete_message(user_id, self.last_inline[user_id].message_id)
        except KeyError:
            pass
        finally:
            self.send_reply_markup(user_id)

    def registration(self, message):
        try:
            if 99999 < int(message.text) < 1000000:
                self.cursor.execute(
                    "update payments set user_id = {0}, payment_number = 0 where payment_number = {1}".format(
                        int(message.chat.id), int(message.text)))
                self.conn.commit()
                self.bot.send_message(message.chat.id, "Ваша учётная запись успешно привязана")
                self.send_reply_markup(self.group_id)
            else:
                self.bot.send_message(message.chat.id, "Код хуйня")
        except ValueError:
            pass

    @staticmethod
    def encrypt_keys(message):
        api_key = message.text
        key = str(message.chat.id)
        encoded = cryptocode.encrypt(api_key, key)
        return encoded

    def decrypt_keys(self, user_id):
        keys = self.get_api_keys_from_db(user_id)
        api_key = cryptocode.decrypt(keys[0], str(user_id))
        api_secret_key = cryptocode.decrypt(keys[1], str(user_id))
        return api_key, api_secret_key

    def set_api_key(self, message):
        encoded = self.encrypt_keys(message)
        if self.check_user_in_keys(message.chat.id):
            self.cursor.execute(
                "update keys set api_key = '{0}' where user_id_keys = {1}".format(encoded, message.chat.id))
        else:
            self.cursor.execute(
                "insert into keys (user_id_keys, api_key) values ({0}, '{1}')".format(message.chat.id, encoded))
        self.conn.commit()
        self.bot.send_message(message.chat.id, "Введите ваш Api secret key")
        self.bot.register_next_step_handler_by_chat_id(message.chat.id, self.set_secret_key)

    def set_secret_key(self, message):
        encoded = self.encrypt_keys(message)
        self.cursor.execute(
            "update keys set api_secret_key = '{0}' where user_id_keys = {1}".format(encoded, message.chat.id))
        self.conn.commit()
        self.bot.send_message(message.chat.id, "Ваши ключи успешно зашифрованы и сохранены")
        self.send_reply_markup(message.chat.id)

    def get_api_keys_from_db(self, user_id):
        self.cursor.execute("select * from keys where user_id_keys = {0}".format(user_id))
        keys = self.cursor.fetchall()[0]
        return keys[1], keys[2]

    def send_reply_markup(self, user_id):
        markup = types.InlineKeyboardMarkup(row_width=2)
        # markup = types.ReplyKeyboardMarkup(row_width=2)
        command1 = types.InlineKeyboardButton('Баланс', callback_data="balance")
        command2 = types.InlineKeyboardButton('Пидор ли женя?', callback_data="pidor")
        command3 = types.InlineKeyboardButton('Открытые позиции', callback_data="positions")
        command4 = types.InlineKeyboardButton('Ошибки', callback_data="errors")
        command5 = types.InlineKeyboardButton('Unrealised pnl', callback_data="pnl")
        command6 = types.InlineKeyboardButton('Дата окончания подписки', callback_data="date")
        markup.add(command1, command2, command3, command4, command5, command6)
        self.last_inline[user_id] = self.bot.send_message(user_id, "Выберите команду:", reply_markup=markup)

    def get_balance(self, user_id):
        try:
            keys = self.decrypt_keys(user_id)
            session = HTTP("https://api.bybit.com", api_key=keys[0], api_secret=keys[1])
            balance = round(session.get_wallet_balance(coin="USDT")['result']['USDT']['equity'], 2)
            self.bot.send_message(user_id, "Ваш баланс USDT: {0}".format(balance))
        except exceptions.InvalidRequestError as ex:
            if ex.message == "invalid api_key":
                self.bot.send_message(user_id,
                                      "Ваши api ключи являются неверными, чтобы обновить ключи "
                                      "используйте команду /api_keys")
            else:
                print(ex)

    def get_positions(self, user_id):
        wb = openpyxl.load_workbook('main.xlsx')
        sheet = wb['Лист1']
        count_row = sheet.max_row
        self.bot.send_message(user_id, self.search_excel_info(count_row, sheet, user_id))

    def search_excel_info(self, count_row, sheet, user_id):
        try:
            positions = ""
            keys = self.decrypt_keys(user_id)
            session = HTTP("https://api.bybit.com", api_key=keys[0], api_secret=keys[1])
            for i in range(count_row - 1):
                row_excel = sheet[f'A{int(i + 2)}'].value
                position = session.my_position(symbol=row_excel)['result'][0]['position_value']
                if position != 0:
                    positions += row_excel + "\n"
            if positions == "":
                positions = "Нет открытых позиций"
            return positions
        except exceptions.InvalidRequestError as ex:
            if ex.message == "invalid api_key":
                return "Ваши api ключи являются неверными, чтобы обновить ключи используйте команду /api_keys"
            else:
                print(ex)

    def get_errors(self):
        if os.path.isfile("errors.txt"):
            if os.path.getsize("errors.txt") != 0:
                with open("errors.txt", 'rb') as file:
                    self.bot.send_document(self.group_id, file)
            else:
                self.bot.send_message(self.group_id, "Ошибок нет")
        else:
            self.bot.send_message(self.group_id, "Ошибок нет")

    def unrealised_pnl(self, user_id):
        try:
            keys = self.decrypt_keys(user_id)
            session = HTTP("https://api.bybit.com", api_key=keys[0], api_secret=keys[1])
            balance = round(session.get_wallet_balance(coin="USDT")['result']['USDT']['unrealised_pnl'], 2)
            self.bot.send_message(user_id, "Ваш unrealised pnl USDT: {0}".format(balance))
        except exceptions.InvalidRequestError as ex:
            if ex.message == "invalid api_key":
                self.bot.send_message(user_id,
                                      "Ваши api ключи являются неверными, чтобы обновить ключи "
                                      "используйте команду /api_keys")
            else:
                print(ex)

    def check_user_in_keys(self, user_id):
        self.cursor.execute("select * from keys where user_id_keys = {0}".format(user_id))
        ans = self.cursor.fetchall()
        if len(ans) == 0:
            self.bot.send_message(user_id,
                                  "У вас отсутсвуют ключи api. Для добавления ключей используйте команду /api_keys")
            return False  # пользователь отсутсвует
        else:
            return True

    def check_user(self, user_id):
        self.cursor.execute("select * from payments where user_id = {0}".format(user_id))
        ans = self.cursor.fetchall()
        if len(ans) == 0:
            return False  # пользователь отсутсвует
        else:
            date = ans[0][2]
            date_now = datetime.now().date()
            if date_now < date:
                return True  # подписка ещё действительна
            else:
                self.bot.send_message(user_id, "Действие вашей подписки закончилось")
                return False  # подписка зкончилась

    def check_date_of_subscription(self, user_id):
        self.cursor.execute("select expiry_date from payments where user_id = {0}".format(user_id))
        self.bot.send_message(user_id, "Дата окончания вашей подписки: {0}".format(self.cursor.fetchall()[0][0]))


if __name__ == "__main__":
    TelegramBot()
