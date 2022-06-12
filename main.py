import telebot
from telebot import types
import config

import psycopg2
import os

import schedule
import time
import threading

# from asyncscheduler import AsyncScheduler

print("Бот запущен. Нажмите Control+Z для завершения")

bot = telebot.TeleBot(config.token)


class User:
        def __init__(self, username, userStatus,userPurposes):
                self.username = username
                self.userStatus = userStatus
                self.userPurposes = userPurposes

class Purpose:
        def __init__(self, purpose, progress, today):
                self.purpose = purpose
                self.progress = progress      
                self.today = today 

user_data = {}          
user_spam = {} 
msgStart = "*Есть такая техника – «тройной молодец». Как она работает?\n\n*Например, ты хочешь начать читать каждый день или бросить вредную привычку, но это требует ежедневных усилий. Наверное ты знаешь, чтобы выработать какую-то привычку, нужен 21 день. Ты делаешь это первый день – отмечаешь в боте и получаешь букву М, второй день – букву О, и так семь дней, пока не соберется слово «МОЛОДЕЦ».\n\n*Чтобы получить своего заветного «тройного молодца» повтори слово «молодец» 3 раза и это поможет в достижении твоей цели 🎯*\n"

msgRegister = "*Напишите ниже*, какую пагубную привычку хотите устранить,\nили какую хорошую привычку Вы *хотите выработать*: \n\nНапример: _Хочу начать читать книги каждый день_\nИли: _Хочу бросить пить!_"

msgCancel = "😟 *Вот так просто сдашься?*\nУ тебя есть еще время до *00:00*, и только тогда будет обнулён весь прогресс!\n"

# Команда start
@bot.message_handler(commands=["start"])
def start(message):
        # print(threading.current_thread())
        if message.from_user.id in user_data:
                msg = showMainMenu(message.from_user.id, 'Главное меню: ')
                bot.register_next_step_handler(msg, mainMenu) 
        else:
                bot.send_message(message.chat.id, msgStart, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
                
                msg = bot.send_message(message.chat.id, msgRegister, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
                bot.register_next_step_handler(msg, inputPurpose)

@bot.message_handler(commands=["notify"])
def changeWeek(message):
        if message.from_user.id == 654953623:
                string = "*Введите текст обновления, которое будет отправлено пользователям: 📩*"
                msg = bot.send_message(message.chat.id, string, parse_mode="Markdown")
                bot.register_next_step_handler(msg, notify_menu)

        else: 
                string = "*У Вас нет доступа к этой команде 🙁*"
                msg = showMainMenu(message.chat.id, string)
                bot.register_next_step_handler(msg, mainMenu)  

def notify_menu(message):
        
        for k,v in user_data.items():
                if v.userStatus != -1: 
                        try: 
                                bot.send_message(k, message.text, parse_mode="Markdown")
                        except Exception as e:
                                print(e)


        msg = showMainMenu(message.chat.id, "*Сообщение успешно отправлено 📬!*")
        bot.register_next_step_handler(msg, mainMenu)


def showProgress(user_id):

        purp = user_data[user_id].userPurposes
        string = "Ваша цель: *" + purp.purpose + "*\n"

        string += "Сегодня: "

        if purp.today == 1:
                string += "*Выполнено* ✅"
        else:
                string += "*Не выполнено* ❌"

        string += "\n_Информация: сегодняшний прогресс будет засчитан в 00 часов 00 минут._"
        bot.send_message(user_id, string, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")



        string = "Общий прогресс: "
        if purp.progress == 0:
                string += "*ты пока не собрал букв, не сдавайся, все впереди!* 😊"
        else:
                string += "*"

                Fellow = 'МОЛОДЕЦ'

                if purp.progress > 7:
                        string += (Fellow + ' ') * (purp.progress // 7) # round(v.userPurposes.progress / 7) math.floor(purp.progress / 7 *10)/10
                        string += Fellow[:(purp.progress % 7)]
                        if purp.progress > 21:
                                bot.send_message(user_id, 'Поздравляем!!! Вы дошли до *3 МОЛОДЦОВ*!', parse_mode="Markdown")
                else: 
                        string += Fellow[:purp.progress]
                string += "*"
        string += "\n"

        return bot.send_message(user_id, string, parse_mode="Markdown")

def showMainMenu(user_id, message):

        mainMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        purp = user_data[user_id].userPurposes

        if purp.today == 1:
                mainMenu.add(types.KeyboardButton("Отменить ❌"))
        else:
                mainMenu.add(types.KeyboardButton("Отметить сегодня ✅"))

        mainMenu.add(types.KeyboardButton("Мой прогресс 📈"))
        mainMenu.add(types.KeyboardButton("Правила игры"))
        return bot.send_message(user_id, message, reply_markup=mainMenu, parse_mode="Markdown")
 
def showCancelMenu(user_id, message):
        
        cMenu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cMenu.row(types.KeyboardButton("Хочу закончить 🙁"), types.KeyboardButton("Хочу выполнить эту цель 😃"), types.KeyboardButton("Хочу начать новую 😃"))
        return bot.send_message(user_id, message, reply_markup=cMenu, parse_mode="Markdown")

def getUsers():

        conn = psycopg2.connect(dbname=config.DATABASE, user=config.USER, 
                        password=config.PASSWORD, host=config.HOST)
        cursor = conn.cursor()
        
        try:
                cursor.execute("SELECT * FROM users")
                users = cursor.fetchall()

                for user in users:
                        user_data[user[1]] = User(user[2], user[3], [])
                print("Database users sucesessful loaded -> ")
                print(users)
        except Exception as e:
                print(e)
                print("Случилась ошибка при получении пользователей!")

        cursor.close()
        conn.close()

def getFellows():

        conn = psycopg2.connect(dbname=config.DATABASE, user=config.USER, 
                password=config.PASSWORD, host=config.HOST)
        cursor = conn.cursor()
        try:
                cursor.execute("SELECT * FROM fellows")
                fellows = cursor.fetchall()

                for fellow in fellows:
                        user_data[fellow[1]].userPurposes = Purpose(fellow[2], fellow[3], fellow[4])
                        # user_data[user[1]] = User(user[2], [])

                print("Database fellows sucesessful loaded -> ")
                print(fellows)
        except Exception as e:
                print(e)
                print("Случилась ошибка при получении пользователей!")
                
        cursor.close()
        conn.close()

def updateUser(user_id):
        
        conn = psycopg2.connect(dbname=config.DATABASE, user=config.USER, 
                        password=config.PASSWORD, host=config.HOST)
        cursor = conn.cursor()

        try:
                purp = user_data[user_id].userPurposes
                
                sql = "UPDATE fellows SET progress= %s,today= %s WHERE user_id= %s"
                val = (purp.progress, purp.today, user_id)
                cursor.execute(sql, val)
                conn.commit()
                print("Цель успешно обновилась!")

                sql = "UPDATE users SET status= %s WHERE user_id= %s"
                val = (user_data[user_id].userStatus, user_id)
                cursor.execute(sql, val)
                conn.commit()
                print(f"Пользователь {user_id} успешно обновился!")

        except Exception as e:
                print(e)
                print("Случилась ошибка при обновлении пользователя!")
        cursor.close()
        conn.close()

def updatePurposes():

        for k,v in user_data.items():

                if v.userStatus == -1: 
                        continue

                if v.userPurposes.today == 0:
                        v.userPurposes.progress = 0
                        v.userStatus += 1
                        updateUser(k)
                        bot.send_message(k, "Вы сегодня не выполнили задание, ваш прогресс обнулился (", parse_mode="Markdown")

                        if v.userStatus >= 2:
                                msg = showCancelMenu(k, f"Вы не выполнили уже {v.userStatus} подряд 😔")
                                bot.register_next_step_handler(msg, cancelMenu) 
                                return 1
                        msg = showMainMenu(k, 'Главное меню')
                        bot.register_next_step_handler(msg, mainMenu) 
                else:
                        v.userPurposes.progress += 1
                        v.userPurposes.today = 0
                        v.userStatus = 0
                        updateUser(k)
                        string = "Поздравляем с успешным пополнением буквы!!!\n Ваш прогресс на сегодня: "
                        string += "*"

                        Fellow = 'МОЛОДЕЦ'
                        if v.userPurposes.progress > 7:
                                string += (Fellow + ' ') * (v.userPurposes.progress // 7)
                                string += Fellow[:(v.userPurposes.progress % 7)]
                                if v.userPurposes.progress == 21:
                                        bot.send_message(k, 'Поздравляем!!! Вы дошли до *3 МОЛОДЦОВ*!', parse_mode="Markdown")
                        else: 
                                string += Fellow[:v.userPurposes.progress]

                        string += "*"
                        msg = showMainMenu(k, string)
                        bot.register_next_step_handler(msg, mainMenu)    

                        
def inputPurpose(message):
        try:
                if message.text == '' or message.from_user.username == '':
                        print("error username")
                        msg = bot.send_message(message.chat.id, msgRegister, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
                        bot.register_next_step_handler(msg, inputPurpose)
                        return 1

                user_data[message.from_user.id] = User(message.from_user.username, 1, Purpose(message.text, 0, 0))

                conn = psycopg2.connect(dbname=config.DATABASE, user=config.USER, 
                        password=config.PASSWORD, host=config.HOST)
                cursor = conn.cursor()

                sql = "INSERT INTO users (user_id, username, status) VALUES (%s, %s, %s)"
                val = (message.from_user.id, message.from_user.username, 1)
                cursor.execute(sql, val)
                conn.commit()

                sql = "INSERT INTO fellows (user_id, fellow, progress, today) VALUES (%s, %s, %s, %s)"
                val = (message.from_user.id, message.text, 0, 0)
                cursor.execute(sql, val)
                conn.commit()

                print(message.from_user.first_name, " присоединился.")

                string = "Отлично 😉\nВаша цель: " + message.text.strip()
                msg = showMainMenu(message.from_user.id, string)
                bot.register_next_step_handler(msg, mainMenu)

                cursor.close()
                conn.close()
                # print(message.text.strip())

        except Exception as e:
                print(e)

def inputPurpose1(message):
        try:

                user_data[message.from_user.id] = User(message.from_user.username, 1, Purpose(message.text, 0, 0))
                
                conn = psycopg2.connect(dbname=config.DATABASE, user=config.USER, 
                        password=config.PASSWORD, host=config.HOST)
                cursor = conn.cursor()
                

                sql = "UPDATE fellows SET fellow=%s, progress=%s, today=%s WHERE user_id=%s"
                val = (message.text, 0, 0, message.from_user.id)
                cursor.execute(sql, val)
                conn.commit()

                print(message.from_user.first_name, " снова присоединился.")

                string = "Отлично 😉\nВаша новая цель: " + message.text.strip()
                msg = showMainMenu(message.from_user.id, string)
                bot.register_next_step_handler(msg, mainMenu)

        except Exception as e:
                print(e)


def cancelMenu(message):
        if message.text.strip().split()[1] == "закончить":
                bot.send_message(message.chat.id, "Жаль, что ты больше не хочешь :(\nТы всегда можешь начать заново, просто напиши /start", parse_mode="Markdown")
                user_data[message.from_user.id].userStatus = -1
                updateUser(message.from_user.id)

        elif message.text.strip().split()[1] == "выполнить":
                bot.send_message(message.chat.id, "Ты сделал *правильный* выбор 😉! Продолжай 👉 /start", parse_mode="Markdown")
                

        elif message.text.strip().split()[1] == "начать":
                msg = bot.send_message(message.chat.id, msgRegister, reply_markup=types.ReplyKeyboardRemove(), parse_mode="Markdown")
                bot.register_next_step_handler(msg, inputPurpose1)


def mainMenu(message):

        if message.from_user.id in user_spam and time.time() - user_spam[message.from_user.id] < 1.5:
                bot.send_message(message.chat.id, "Перестань спамить бота )", parse_mode="Markdown")
                return 1
        user_spam[message.from_user.id] = time.time()
        # print(threading.current_thread())
        if message.text.strip().split()[0] == "Отметить":
                purp = user_data[message.from_user.id].userPurposes
                purp.today = 1
                user_data[message.from_user.id].userStatus = 0
                updateUser(message.from_user.id)

                string = 'Хорошая работа, ты сегодня молодец! 😊'
                msg = showMainMenu(message.from_user.id, string)
                bot.register_next_step_handler(msg, mainMenu)

        elif message.text.strip().split()[0] == "Отменить":
                purp = user_data[message.from_user.id].userPurposes
                purp.today = 0
                updateUser(message.from_user.id)

                msg = showMainMenu(message.from_user.id, msgCancel)
                bot.register_next_step_handler(msg, mainMenu)

        elif message.text.strip().split()[0] == "Мой":
                msg = showProgress(message.from_user.id)
                bot.register_next_step_handler(msg, mainMenu)


        elif message.text.strip().split()[0] == "Правила":
                msg = bot.send_message(message.chat.id, msgStart, parse_mode="Markdown")
                bot.register_next_step_handler(msg, mainMenu)
        
        # else:
        #         msg = showMainMenu(message.from_user.id, 'Главное меню:')


@bot.message_handler(content_types=["text"])
def handle_text(message):
        if message.from_user.id in user_data:

                if message.text.strip().split()[0] == "Отметить":
                        purp = user_data[message.from_user.id].userPurposes
                        purp.today = 1
                        updateUser(message.from_user.id)

                        string = 'Хорошая работа, ты сегодня молодец! 😊'
                        msg = showMainMenu(message.from_user.id, string)
                        bot.register_next_step_handler(msg, mainMenu)

                elif message.text.strip().split()[0] == "Отменить":
                        purp = user_data[message.from_user.id].userPurposes
                        purp.today = 0
                        updateUser(message.from_user.id)

                        # string = 'Жаль конечно, но придется начать собирать слово заново 😅'
                        msg = showMainMenu(message.from_user.id, msgCancel)
                        bot.register_next_step_handler(msg, mainMenu)

                elif message.text.strip().split()[0] == "Мой":
                        msg = showProgress(message.from_user.id)
                        bot.register_next_step_handler(msg, mainMenu)


                elif message.text.strip().split()[0] == "Правила":
                        msg = bot.send_message(message.chat.id, msgStart, parse_mode="Markdown")
                        bot.register_next_step_handler(msg, mainMenu)

        else: bot.send_message(message.chat.id, 'Вы не зарегистрированы! Используйте /start', parse_mode="Markdown")
        print(threading.current_thread())

    
bot.enable_save_next_step_handlers(delay=3)

bot.load_next_step_handlers()

def main():
        getUsers()
        getFellows()

        schedule.every().day.at("00:00").do(updatePurposes)

        thr1 = threading.Thread(target=myfunc)
        thr1.start()

def myfunc():
        while True:
                schedule.run_pending()
                time.sleep(30)       

if __name__== '__main__':

        main()
        bot.polling(none_stop=True) # , interval=0
