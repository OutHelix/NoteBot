import os
import discord
from discord.ext import commands
import datetime

# from config import *
import psycopg2

settings = {
    'token': 'token',
    'bot': 'NoteNot',
    'id': 1103810068840984586,
    'prefix': '/'
}

intents = discord.Intents.default()
intents.message_content = True

# установка префикса
bot = commands.Bot(command_prefix=settings['prefix'], intents=intents)

# подключение базы данных
conn = psycopg2.connect(database="NoteBook", user="postgres", password="127576", host="localhost", port="5432")
cursor = conn.cursor()


# проверка на пользователя в отдельной функции
def check_user(ctx):
    id_user = ctx.author
    cursor.execute(f"SELECT * FROM service.users WHERE discord=%s", (str(id_user),))
    records = list(cursor.fetchall())
    if not records:
        return 'not_registered'
    else:
        return 1


# команда на проверку пользователя -check
@bot.command()
async def check(ctx):
    if check_user(ctx) == 1:
        await ctx.reply('Проверка: вы зарегистрированы!')
    else:
        await ctx.reply('Проверка: вы не зарегистрированы!')


@bot.command()
async def note(ctx):
    # проверка на регистрацию пользователя
    if check_user(ctx) == 1:
        # забор текста заметки
        noted = str(ctx.message.content).split(settings['prefix'] + 'note')[1][1:]
        # если пользователь ввел только команду:
        if not noted:
            await ctx.reply(f"Что бы сделать заметку: {settings['prefix']}note [текст]")
        else:
            # добавляем реакции
            message = await ctx.reply('Вы уверены что хотите сделать эту заметку?')
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            def check_answer(reaction, user):
                return user == ctx.author

            try:
                # проверка нажатия на ту или иную реакцию
                reaction, user = await bot.wait_for("reaction_add", timeout=120, check=check_answer)
                await message.remove_reaction(reaction, user)
                if str(reaction.emoji) == '✅':
                    add_note(noted, ctx)
                    await message.edit(content='**_Заметка добавлена успешно._**')
                    await message.clear_reactions()

                if str(reaction.emoji) == '❌':
                    await message.edit(content='**_Добавление заметки отменено._**')
                    await message.clear_reactions()
            except TimeoutError:
                message.edit(content='**_Добавление заметки отменено. Время вышло._**')
                await message.clear_reactions()
    else:
        await ctx.reply('Зарегистрируйтесь')


def all_notes_user(ctx):
    # получаем имя пользователя
    id_user = ctx.author
    # вытаскиваем id в БД
    cursor.execute("SELECT * FROM service.users WHERE discord=%s", (str(id_user),))
    id_user = list(cursor.fetchall())[0][0]

    # вытаскиваем все заметки current пользователя
    cursor.execute("SELECT * FROM service.notes WHERE id_user=%s", (str(id_user),))
    notes = list(cursor.fetchall())
    return notes, id_user


def add_note(noted, ctx):
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


@bot.command()
async def all_notes(ctx):
    if check_user(ctx) == 1:
        notes, id_user = all_notes_user(ctx)
        if not notes:
            await ctx.reply(f"У вас еще нет заметок.\n**Что бы сделать заметку: "
                            f"{settings['prefix']}note [текст]**")
        else:
            mess_notes = ''
            for note_user in notes:
                mess_notes += f"Заметка {note_user[1]} от *{time(note_user[1])}*: " \
                              f"`{text_notes(note_user[1], id_user, 1)}`\n"
            await ctx.reply(mess_notes)
    else:
        await ctx.reply('Зарегистрируйтесь')


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


@bot.command()
async def take_note(ctx):
    if check_user(ctx) == 1:
        num_note = str(ctx.message.content).split(settings['prefix'] + 'take_note')[1][1:]
        if not num_note:
            await ctx.reply(f"Что бы выбрать заметку: {settings['prefix']}take_note [№ заметки]")
        else:
            id_user = ctx.author
            # вытаскиваем id из БД
            cursor.execute("SELECT * FROM service.users WHERE discord=%s", (str(id_user),))
            id_user = list(cursor.fetchall())[0][0]
            await ctx.reply(f"_{num_note} заметка от {time(num_note)}:_\n```{text_notes(num_note, id_user, 2)}```")
    else:
        await ctx.reply('Зарегистрируйтесь')


@bot.command()
async def delete_note(ctx):
    if check_user(ctx) == 1:
        delete_note = str(ctx.message.content).split(settings['prefix'] + 'delete_note')[1][1:]
        if not delete_note:
            await ctx.reply(f"Что бы удалить заметку: {settings['prefix']}delete_note [№ заметки]")
        else:
            message = await ctx.reply('Вы уверены что хотите удалить эту заметку?')
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            def check_answer(reaction, user):
                return user == ctx.author

            try:
                # проверка нажатия на ту или иную реакцию
                reaction, user = await bot.wait_for("reaction_add", timeout=120, check=check_answer)
                await message.remove_reaction(reaction, user)
                if str(reaction.emoji) == '✅':
                    del_note_func(ctx, delete_note)
                    await message.edit(content='**_Заметка удалена успешно._**')
                    await message.clear_reactions()

                if str(reaction.emoji) == '❌':
                    await message.edit(content='**_Удаление заметки отменено._**')
                    await message.clear_reactions()
            except TimeoutError:
                message.edit(content='**_Удаление заметки отменено. Время вышло._**')
                await message.clear_reactions()

    else:
        await ctx.reply('Зарегистрируйтесь')


def del_note_func(ctx, delete_note):
    id_user = all_notes_user(ctx)[1]
    os.remove(f'F:\\NoteBot\\notes\\{id_user}\\{delete_note}.txt')
    cursor.execute(f"DELETE FROM service.notes WHERE id_user={id_user} AND note_id={delete_note}")
    conn.commit()


def start_ds():
    bot.run(settings['token'])
