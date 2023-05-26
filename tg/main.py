import os
import telebot
from telebot import types
import datetime
import psycopg2

bot = telebot.TeleBot('token')

conn = psycopg2.connect(database="NoteBook", user="postgres", password="127576", host="localhost", port="5432")
cursor = conn.cursor()


@bot.message_handler(commands=['check'])
def bot_check(message):
    if check_user(message) == 1:
        bot.send_message(message.chat.id, text='<b>Вы зарегистрированы</b>', parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, text='<b>Вы не зарегистрированы</b>', parse_mode='HTML')


# проверка на пользователя в отдельной функции
def check_user(message):
    print(message.from_user.username)
    id_user = '@' + message.from_user.username
    cursor.execute(f"SELECT * FROM service.users WHERE telegram=%s", (str(id_user),))
    records = list(cursor.fetchall())
    if not records:
        return 'not_registered'

    else:
        return 1


@bot.message_handler(commands=['note'])
def note(message):
    # проверка на регистрацию пользователя
    if check_user(message) == 1:
        noted = str(message.text).split('/note')
        print(noted)
        if not noted[1]:
            bot.send_message(message.chat.id, text='Что бы сделать заметку: /note [текст]')
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Да')
            btn2 = types.KeyboardButton('Нет')
            markup.add(btn1, btn2)
            bot.send_message(message.chat.id, text='<b>Вы уверены, что хотите сделать эту заметку?</b>',
                             parse_mode='HTML', reply_markup=markup)
            bot.register_next_step_handler(message, check_answer, noted)
    else:
        bot.send_message(message.chat.id, text='Пожалуйста, зарегистрируйтесь, чтобы делать заметки!')


def check_answer(message, noted):
    if message.text == "Да":
        bot.send_message(message.chat.id, text='Заметка успешно добавлена', reply_markup=types.ReplyKeyboardRemove())
        add_note(noted[1], message)
    if message.text == "Нет":
        bot.send_message(message.chat.id, text='Добавление заметки отменено', reply_markup=types.ReplyKeyboardRemove())


def all_notes_user(message):
    # получаем имя пользователя
    if check_user(message) == 1:
        id_user = f'@{message.from_user.username}'
        # вытаскиваем id в БД
        cursor.execute("SELECT * FROM service.users WHERE telegram=%s", (str(id_user),))
        id_user = list(cursor.fetchall())[0][0]

        # вытаскиваем все заметки current пользователя
        cursor.execute("SELECT * FROM service.notes WHERE id_user=%s", (str(id_user),))
        notes = list(cursor.fetchall())
        print(notes, id_user)
        return notes, id_user
    else:
        bot.send_message(message.chat.id, text='Вы не зарегистрированы!')


@bot.message_handler(commands=['all_notes'])
def take_notes(message):
    if check_user(message) == 1:
        notes, id_user = all_notes_user(message)
        if not notes:
            bot.send_message(message.chat.id, text="У вас еще нет заметок.\nЧто бы сделать заметку: "
                                                   "<b>/note [текст]</b>", parse_mode='HTML')
        else:
            mess_notes = ''
            for note_user in notes:
                mess_notes += f"<b>Заметка {note_user[1]}</b>, от <i>{time(note_user[1])}</i>: " \
                              f"{text_notes(note_user[1], id_user, 1)}\n"
            bot.send_message(message.chat.id, mess_notes, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 'Зарегистрируйтесь')


def time(number):
    cursor.execute("SELECT note_time FROM service.notes WHERE note_id=%s", (str(number),))
    a = cursor.fetchone()[0]
    print(a)
    return a


def text_notes(number, id_user, op):
    if op == 1:
        note_user = open(f'F:\\NoteBot\\notes\\{id_user}\\{number}.txt', 'r')
        a = str(note_user.read())
        if len(list(a)) > 25:
            a = a[0:25] + '...'
        return a
    elif op == 2:
        note_user = open(f'F:\\NoteBot\\notes\\{id_user}\\{number}.txt', 'r')
        a = str(note_user.read())
        return a


def add_note(noted, ctx):
    print(noted)
    print(type(noted))
    notes, id_user = all_notes_user(ctx)
    # прибавляем к id последней заметке 1 и записываем ее
    if not notes:
        number = 1
    else:
        number = notes[len(notes) - 1][1] + 1

    # если в папке нет пользователя -> создаем ее
    if not os.path.isdir(f'F:\\NoteBot\\notes\\{id_user}'):
        path = f'F:\\NoteBot\\notes\\{id_user}'
        os.mkdir(path)

    # создаем текстовый файл с Id заметки
    note_user = open(f'F:\\NoteBot\\notes\\{id_user}\\{number}.txt', 'w')
    # пробуем записать заметку
    try:
        note_user.write(noted)
    finally:
        note_user.close()

    # вносим изменения в БД (записываем id пользователя, заметки и время создания)
    cursor.execute('INSERT INTO service.notes(id_user, note_id, note_time) VALUES (%s, %s, %s);',
                   (str(id_user), str(number), str(datetime.datetime.now())[:19]))
    conn.commit()


@bot.message_handler(commands=['delete_note'])
def del_note(message):
    if check_user(message) == 1:
        delete_note = message.text.split('/delete_note')
        print(delete_note)
        delete_note = delete_note[1][1:]
        if not delete_note:
            bot.send_message(message.chat.id, "Чтобы удалить заметку: /delete_note [№ заметки]")
        else:
            try:
                del_note_func(message, delete_note)
                bot.send_message(message.chat.id, "Заметка успешно удалена!")
            except:
                pass
    else:
        bot.send_message(message.chat.id, "Вы не зарегистрированы!")


def del_note_func(ctx, delete_note):
    id_user = all_notes_user(ctx)[1]
    os.remove(f'F:\\NoteBot\\notes\\{id_user}\\{delete_note}.txt')
    cursor.execute(f"DELETE FROM service.notes WHERE id_user={id_user} AND note_id={delete_note}")
    conn.commit()


def start_tg():
    bot.infinity_polling()
