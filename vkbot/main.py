import datetime
import os

# from config import token, id
import psycopg2
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

token = 'token'
id = 220461380

vk_session = vk_api.VkApi(token=token)
longpoll = VkBotLongPoll(vk_session, id)
VK = vk_session.get_api()


conn = psycopg2.connect(database="NoteBook", user="postgres", password="127576", host="localhost", port="5432")
cursor = conn.cursor()


def send_message(id, text):
    try:
        vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': get_random_id()})
    except:
        vk_session.method('messages.send', {'domain': id, 'message': text, 'random_id': get_random_id()})


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


def check(id):
    cursor.execute(f"SELECT * FROM service.users WHERE vk='@{id}'")
    records = list(cursor.fetchall())
    if not records:
        domain = vk_session.method("users.get", {"user_ids": id, 'fields': 'domain'})
        domain = domain[0]['domain']
        cursor.execute(f"SELECT * FROM service.users WHERE vk='@{domain}'")
        records = list(cursor.fetchall())
        if not records:
            return False
        else:
            return True
    else:
        return True


def all_notes_user(id):
    # получаем имя пользователя
    if check(id):
        id_user = id
        print(id_user)
        # вытаскиваем id в БД
        cursor.execute("SELECT * FROM service.users WHERE vk=%s", (str(f'@{id_user}'),))
        s = cursor.fetchall()
        if not s:
            domain = vk_session.method("users.get", {"user_ids": id, 'fields': 'domain'})
            domain = domain[0]['domain']
            cursor.execute("SELECT * FROM service.users WHERE vk=%s", (str(f'@{domain}'),))
            s = cursor.fetchall()
        print(s)
        id_user = s[0][0]
        # вытаскиваем все заметки current пользователя
        cursor.execute("SELECT * FROM service.notes WHERE id_user=%s", (str(id_user),))
        notes = list(cursor.fetchall())
        return notes, id_user
    else:
        send_message(id, 'Вы не зарегистрированы!')


def take_notes(id):
    if check(id):
        notes, id_user = all_notes_user(id)
        if not notes:
            send_message(id, "У вас еще нет заметок.\nЧто бы сделать заметку: /note [текст]")
        else:
            mess_notes = ''
            for note_user in notes:
                mess_notes += f"Заметка {note_user[1]} от {time(note_user[1])}: " \
                              f"{text_notes(note_user[1], id_user, 1)}\n"
            send_message(id, mess_notes)
    else:
        send_message(id, 'Зарегистрируйтесь')


def note(text, id):
    # проверка на регистрацию пользователя
    if check(id):
        noted = str(text).split('/note')
        print(noted)
        if not noted[1]:
            send_message(id, 'Что бы сделать заметку: /note [текст]')

        else:
            send_message(id, 'Заметка успешно добавлена')
            add_note(noted[1], id)

    else:
        send_message(id, 'Пожалуйста, зарегистрируйтесь, чтобы делать заметки!')


def add_note(noted, id):
    notes, id_user = all_notes_user(id)
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


def del_note(message, id):
    if check(id):
        delete_note = message.split('/delete_note')
        delete_note = delete_note[1][1:]
        if not delete_note:
            send_message(id, 'Чтобы удалить заметку: /delete_note [№ заметки]')
        else:
            del_note_func(id, delete_note)
            send_message(id, "Заметка успешно удалена!")
    else:
        send_message(id, "Вы не зарегистрированы!")


def del_note_func(id, delete_note):
    try:
        id_user = all_notes_user(id)[1]
        os.remove(f'F:\\NoteBot\\notes\\{id_user}\\{delete_note}.txt')
        cursor.execute(f"DELETE FROM service.notes WHERE id_user={id_user} AND note_id={delete_note}")
        conn.commit()
    finally:
        send_message(id, "Выбранной заметки не существует.")


def start_vk():
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            # Команда /check
            if event.object.message['text'].lower() == '/check':
                if check(event.message['from_id']):
                    send_message(event.message['from_id'], 'Вы зарегистрированы!')
                else:
                    send_message(event.message['from_id'], 'Вы не зарегистрированы!')

            # Команда /note
            elif '/note' in event.object.message['text'].lower():
                # Проверка на регистрацию
                if check(event.message['from_id']):
                    note(event.message['text'].lower(), event.message['from_id'])

            # Команда /all_notes
            elif event.object.message['text'].lower() == '/all_notes':
                # Проверка на регистрацию
                if check(event.message['from_id']):
                    take_notes(event.message['from_id'])

            # Команда /del_note
            elif '/delete_note' in event.object.message['text'].lower():
                del_note(event.object.message['text'], event.message['from_id'])
