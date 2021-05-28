# -*- coding: utf-8 -*-
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import os
import json
import requests
from requests.auth import HTTPBasicAuth
from sys import argv

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def receive_update():

    if request.method == "POST":
        def set_close_client_application(update: Update, _: CallbackContext) -> None:
            dialog_number = update.effective_message.reply_markup['inline_keyboard'][-1][-1]['callback_data']


            response = requests.request("PUT", url, headers=headers, data=payload)
            try:
                error_message = 'ошибка закрытия заявки ' + (json.loads(response.text)).get('errors')
            except:
                pass
            query.message.reply_text(success_message) if response.status_code == 200 else query.message.reply_text(
                error_message
            )

        def start(update: Update, _: CallbackContext) -> None:
            pass

        def help_command(update: Update, _: CallbackContext) -> None:
            update.message.reply_text("Use /start to test this bot.")

        text = ""
        fullname = ""
        data = request.get_json()
        dict_data = data.get("client")
        phone = dict_data.get("phone")
        name = dict_data.get("name")
        dialog_id = data.get("dialog_id")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("закрыть заявку", callback_data=dialog_id)],
        ])

        updater = Updater(TELEGRAM_BOT_TOKEN)
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CallbackQueryHandler(set_close_client_application))
        updater.dispatcher.add_handler(CommandHandler('help', help_command))
        updater.start_polling()

        if name is not None:
            fullname = name
        if data["photo"] is not None:
            updater.bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                                     text=data["transport"] +
                                     "(" + phone + ")" +
                                     "  " + fullname +
                                     "\n" + text +
                                     data["photo"],
                                     reply_markup=keyboard)
        elif data["pdf"] is not None:
            updater.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=(
                    data["transport"] +
                    "(" + phone + ")" +
                    "  " + fullname +
                    "\n" + text + "\n" +
                    data["pdf"]
                    ))
        elif data["attachments"]:
            updater.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=(
                    data["transport"] +
                    "(" + phone + ")" +
                    "  " + fullname + "\n" +
                    text + "\n" +
                    (data["attachments"][0].get("file").get("url")))
                            )
        print(data)
    return {"ok": True}


if __name__ == "__main__":
    if len(argv) == 2:
        app.run(host=HOST, port=int(argv[1]))
    else:
        app.run(host=HOST, port=PORT)
