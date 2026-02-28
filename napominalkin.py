import os
import json
import threading
import telebot
import time
from datetime import datetime
from zoneinfo import ZoneInfo

token = os.environ.get("TOKEN")

bot = telebot.TeleBot(token)
data_file = "tasks.json"
time_file = "dates.json"

try:
    with open(time_file, "r") as file:
        time_data = json.load(file)
except Exception as error:
    time_data = {}

try:
    with open(data_file, "r") as file:
        user_data = json.load(file)
except Exception as error:
    user_data = {}


def save_tasks_file():
    with open(data_file, "w") as file:
        json.dump(user_data, file, indent=4)


def save_time_file():
    with open(time_file, "w") as file:
        json.dump(time_data, file, indent=4)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if chat_id not in user_data:
        user_data[chat_id] = {}
        save_tasks_file()
    name = str(message.from_user.first_name)

    bot.send_message(message.chat.id, f"Привет {name}!")
    bot.send_message(message.chat.id, "Если хочешь ознакомиться с моим функционалом, введи /help")


@bot.message_handler(commands=["add"])
def add_element(message):
    element = message.text.replace("/add", "").strip()
    bot.send_message(message.chat.id,
                     f"Теперь напиши мне дату и время, когда тебе напомнить про это событие, в формате 'дд.мм.гггг чч:мм'")

    bot.register_next_step_handler_by_chat_id(message.chat.id, lambda msg: process_user_input(msg, element))


def process_user_input(message, element):
    chat_id = str(message.chat.id)
    date_time = message.text.strip()
    try:
        parsed_time = datetime.strptime(date_time, "%d.%m.%Y %H:%M")
        parsed_time = parsed_time.replace(tzinfo=ZoneInfo("Europe/Moscow"))
    except ValueError:
        bot.send_message(message.chat.id, f"Некорректный вид даты и времени.")
    else:
        current_time = datetime.now(ZoneInfo("Europe/Moscow"))
        if current_time >= parsed_time:
            bot.send_message(message.chat.id, "Эта дата уже прошла. Дата должна быть в будущем времени.")
            return
        if date_time not in user_data[chat_id]:
            if date_time not in time_data:
                time_data[date_time] = list()
                time_data[date_time].append(message.chat.id)
                save_time_file()
                user_data[chat_id][date_time] = []
                user_data[chat_id][date_time].append(element)
                user_data[chat_id][date_time].append(len(user_data[chat_id]))
                save_tasks_file()
                bot.send_message(message.chat.id, f"Задача '{element}' с временем '{date_time}' успешно добавлена.")
            else:
                time_data[date_time].append(message.chat.id)
                save_time_file()
                user_data[chat_id][date_time] = []
                user_data[chat_id][date_time].append(element)
                user_data[chat_id][date_time].append(len(user_data[chat_id]))
                save_tasks_file()
                bot.send_message(message.chat.id, f"Задача '{element}' с временем '{date_time}' успешно добавлена.")
        else:
            bot.send_message(message.chat.id, f"Задача с таким временем уже есть в твоём списке.")


@bot.message_handler(commands=["list"])
def give_list(message):
    chat_id = str(message.chat.id)
    if len(user_data[chat_id]) == 0:
        bot.send_message(message.chat.id, "Похоже твой список пуст.")
    else:
        spisok = "Список элементов: \n\n"
        tasks_date = list(user_data[chat_id])
        for i in tasks_date:
            spisok += (f"{user_data[chat_id][str(i)][1]}) событие: {user_data[chat_id][str(i)][0]}.\n"
                       f" дата: {i}.\n\n")
        bot.send_message(message.chat.id, spisok)


@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(message.chat.id, "Я буду напоминать о событиях, которые ты в меня запишешь!\n\n"
                                      "Что бы добавить в меня событие, напиши /add 'твоё событие' и отправь мне\n"
                                      "Например:  '/add сходить в магазин'\n"
                                      "После отправки события напиши дату и время, когда тебе надо про него напомнить, в формате\n"
                                      "'день.месяц.год часы:минуты'\n"
                                      "Например: '25.01.2026 09:24'\n\n"
                                      "Что бы вывести список твоих задач, напиши /give\n\n"
                                      "Если хочешь удалить из списка задачу, введи /delete 'номер задачи,\n"
                                      "как в списке задач (посмотреть можно в /list)'\n"
                                      "Например:  '/delete 2'")


@bot.message_handler(commands=["delete"])
def delete(message):
    chat_id = str(message.chat.id)
    deleted_element = ""
    date = ""
    try:
        id_delete = int(message.text.replace("/delete", "").strip())
    except ValueError:
        bot.send_message(message.chat.id, "Некорректное число")
    else:
        if 0 < id_delete <= len(user_data[chat_id]):
            id = 0
            for i in user_data[chat_id]:
                if user_data[chat_id][i][1] == id_delete:
                    date = i
                    deleted_element = user_data[chat_id][i][0]
                    del user_data[chat_id][i]
                    save_tasks_file()
                    break
            for i in time_data[date]:
                if str(i) == chat_id:
                    delete = time_data[date].pop(id)
                id += 1
                save_time_file()
                break
            if time_data[date] == []:
                del time_data[date]
                save_time_file()
            bot.send_message(message.chat.id, f"Задача '{deleted_element}' успешно удалена!")
            for i in user_data[chat_id]:
                if id_delete <= user_data[chat_id][i][1]:
                    user_data[chat_id][i][1] -= 1
            save_tasks_file()

        else:
            bot.send_message(message.chat.id, "У вас нет задачи с таким номером")


def time_check():
    while True:
        now_time = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
        if now_time in time_data:
            for i in time_data[now_time]:
                task = user_data[str(i)][now_time]
                bot.send_message(i, f"Напоминаю про событие: '{task[0]}'.")
                del time_data[now_time]
                save_time_file()
                del user_data[str(i)][now_time]
                save_tasks_file()
        time.sleep(30)


timer_thread = threading.Thread(target=time_check)
timer_thread.daemon = True
timer_thread.start()

bot.polling(none_stop=True)
