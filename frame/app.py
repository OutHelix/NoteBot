from flask import Flask, render_template, request, redirect
import psycopg2


app = Flask(__name__)
conn = psycopg2.connect(database="NoteBook", user="postgres", password="127576", host="localhost", port="5432")

cursor = conn.cursor()


@app.route('/login/', methods=['GET'])
def index():
    return render_template('login.html')


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        if request.form.get('login'):
            username = request.form.get('username')
            password = request.form.get('password')

            if not username:
                return render_template('login.html', error="Пожалуйста, введите логин!")
            if not password:
                return render_template('login.html', error="Пожалуйста, введите пароль!")

            cursor.execute("SELECT * FROM service.users WHERE login=%s AND password=%s", (str(username), str(password)))
            records = list(cursor.fetchall())
            if not records:
                return render_template('login.html', error="Введенного вами пользователя не существует!")
            print(records)
            return render_template('account.html', full_name=records[0][1], login=username, password=password,
                                   telegram=records[0][4], discord=records[0][5], vk=records[0][6])

        elif request.form.get('registration'):
            return redirect('/registration/')
    return render_template('login.html')


@app.route('/registration/', methods=['POST', 'GET'])
def registration():
    if request.method == 'POST':
        if request.form.get('login_back'):
            return redirect('/login/')
        else:
            name = request.form.get('name')
            log1n = request.form.get('login')
            password = request.form.get('password')
            telegram = request.form.get('telegram')
            discord = request.form.get('discord')
            vk = request.form.get('vk')
            print(log1n, telegram, discord, vk)
            if not name:
                return render_template('registration.html', error="Пожалуйста, введите ФИ!")
            if not log1n:
                return render_template('registration.html', error="Пожалуйста, введите логин!")
            if not password:
                return render_template('registration.html', error="Пожалуйста, введите пароль!")
            if not telegram:
                return render_template('registration.html', error="Пожалуйста, заполните поле Telegram!")
            if not discord:
                return render_template('registration.html', error="Пожалуйста, заполните поле Discord!")
            if not vk:
                return render_template('registration.html', error="Пожалуйста, заполните поле Vk!")
            cursor.execute('INSERT INTO service.users(full_name, login, password, telegram, discord, vk) VALUES'
                           ' (%s, %s, %s, %s, %s, %s);', (str(name), str(log1n), str(password), str(telegram),
                                                          str(discord), str(vk)))
            conn.commit()
            return redirect('/login/')

    return render_template('registration.html')


def start_app():
    app.run(port=8000, host='127.0.0.1')
