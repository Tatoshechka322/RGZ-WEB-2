from flask import Flask, session, render_template, redirect, request, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import psycopg2


app = Flask(__name__)


app.secret_key = 'smell'  # Ключ для сессий


def dbConnect():
    conn = psycopg2.connect(
        host="127.0.0.1",
        database="cinema",
        user="tkach",
        password="stink")

    return conn


def dbClose(cursor, conn):
    # Закрываем курсор и соединение
    # Порядок важен!
    cursor.close()
    conn.close()


@app.route('/')
def start():
    return redirect(url_for('main'))


@app.route("/app/index", methods=['GET', 'POST'])
def main():

    conn = dbConnect()
    cur = conn.cursor()

    if 'name' not in session:
        return redirect(url_for('registerPage'))

    cur.execute("SELECT * FROM users;")

    result = cur.fetchall()

    visibleUser = session.get('name', 'Anon')

    return render_template('index.html', name=visibleUser, result=result)


@app.route('/app/register', methods=['GET', 'POST'])
def registerPage():
    errors = []

    if request.method == 'GET':
        return render_template("register.html", errors=errors)

    name = request.form.get('name')
    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password):
        errors.append("Пожалуйста, заполните все поля")
        print(errors)
        return render_template("register.html", errors=errors)
    elif not name:
        errors.append("Пожалуйста, заполните все поля")
        print(errors)
        return render_template("register.html", errors=errors)

    hashPassword = generate_password_hash(password)

    conn = dbConnect()
    cur = conn.cursor()

    cur.execute("SELECT username FROM users WHERE username = '%s';" % (username))
    cur.execute("SELECT username FROM users WHERE name = '%s';" % (name))
    cur.execute("SELECT name FROM users WHERE name = '%s';" % (name))

    resultСur = cur.fetchone()

    if resultСur != None:
        errors.append('Пользователь с данным именем уже существует')

        dbClose(cur, conn)

        return render_template('register.html', errors=errors, resultСur=resultСur)

    cur.execute(f"CREATE USER {username} WITH PASSWORD '{hashPassword}';")
    cur.execute("INSERT INTO users (username, password, name) VALUES (%s, %s, %s);", (username, hashPassword, name))

    conn.commit()
    dbClose(cur, conn)

    return redirect("/app/login")


@app.route('/app/login', methods=["GET", "POST"])
def loginPage():
    errors = []

    if request.method == 'GET':
        return render_template("login.html", errors=errors)

    name = request.form.get("name")
    username = request.form.get("username")
    password = request.form.get("password")

    if not (username or password or name):
        errors.append("Пожалуйста, заполните все поля")
        return render_template("login.html", errors=errors)

    conn = dbConnect()
    cur = conn.cursor()

    cur.execute("SELECT name, id, password FROM users WHERE username = %s", (username,))

    result = cur.fetchone()

    if result is None:
        errors.append('Неправильный пользователь или пароль')
        dbClose(cur, conn)
        return render_template("login.html", errors=errors)

    name, userID, hashPassword = result

    if check_password_hash(hashPassword, password):

        session['name'] = name
        session['id'] = userID
        session['username'] = username
        dbClose(cur, conn)
        return redirect("index")

    else:
        errors.append("Неправильный логин или пароль")
        return render_template("login.html", errors=errors)


@app.route("/app/new_session", methods=["GET", "POST"])
def createSession():
    username = session.get('username')
    errors = []

    if username == 'admin':
        if request.method == 'POST':
            movie = request.form.get('movie')
            start_time = request.form.get('date')
            room_number = request.form.get('room_number')

            if start_time:
                try:
                    # Преобразовываем строку в объект datetime
                    time = datetime.strptime(start_time, "%d-%m-%Y %H:%M")
                except ValueError:
                    errors.append('Некорректный формат времени')
                    return render_template('new_session.html', errors=errors)

                conn = dbConnect()
                cur = conn.cursor()

                cur.execute("INSERT INTO cinema_sessions(movie, room_number, start_time) VALUES (%s, %s, %s) RETURNING session_id;", (movie, room_number, time))

                cinema_session_id = cur.fetchone()[0]

                conn.commit()
                dbClose(cur, conn)

                if movie and start_time and room_number:
                    return redirect(url_for('allFilms'))
                else:
                    errors.append('Заполните все поля')
                    return render_template('new_session.html', errors=errors)
        return render_template('new_session.html', errors=errors)


@app.route("/app/all_sessions", methods=["GET", "POST"])
def allFilms():
    conn = dbConnect()
    cur = conn.cursor()

    # Выбираем все киносеансы из таблицы
    cur.execute("SELECT DISTINCT movie FROM cinema_sessions;")
    movie_sessions = cur.fetchall()

    dbClose(cur, conn)

    return render_template("allFilms.html", movie_sessions=movie_sessions)


@app.route("/app/movieSessions/<movie>")
def movie_sessions(movie):
    conn = dbConnect()
    cur = conn.cursor()

    # Выбери все сеансы для конкретного фильма из базы данных
    cur.execute("SELECT * FROM cinema_sessions WHERE movie = %s;", (movie,))
    sessions = cur.fetchall()

    dbClose(cur, conn)

    return render_template("movieSessions.html", movie=movie, sessions=sessions)


@app.route('/app/session/<int:cinema_session_id>')
def session_details(cinema_session_id):
    conn = dbConnect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM cinema_sessions WHERE session_id = %s;", (cinema_session_id,))
    session_data = cur.fetchone()

    # Выберем статусы всех мест
    cur.execute("SELECT seat_1 as seat_1, seat_2 as seat_2, seat_3 as seat_3, seat_4 as seat_4, seat_5 as seat_5, seat_6 as seat_6, seat_7 as seat_7, seat_8 as seat_8, seat_9 as seat_9, seat_10 as seat_10, seat_11 as seat_11, seat_12 as seat_12, seat_13 as seat_13, seat_14 as seat_14, seat_15 as seat_15, seat_16 as seat_16, seat_17 as seat_17, seat_18 as seat_18, seat_19 as seat_19, seat_20 as seat_20, seat_21 as seat_21, seat_22 as seat_22, seat_23 as seat_23, seat_24 as seat_24, seat_25 as seat_25, seat_26 as seat_26, seat_27 as seat_27, seat_28 as seat_28, seat_29 as seat_29, seat_30 as seat_30, occupant_1 as occupant_1, occupant_2 as occupant_2, occupant_3 as occupant_3, occupant_4 as occupant_4, occupant_5 as occupant_5, occupant_6 as occupant_6, occupant_7 as occupant_7, occupant_8 as occupant_8, occupant_9 as occupant_9, occupant_10 as occupant_10, occupant_11 as occupant_11, occupant_12 as occupant_12, occupant_13 as occupant_13, occupant_14 as occupant_14, occupant_15 as occupant_15, occupant_16 as occupant_16, occupant_17 as occupant_17, occupant_18 as occupant_18, occupant_19 as occupant_19, occupant_20 as occupant_20, occupant_21 as occupant_21, occupant_22 as occupant_22, occupant_23 as occupant_23, occupant_24 as occupant_24, occupant_25 as occupant_25, occupant_26 as occupant_26, occupant_27 as occupant_27, occupant_28 as occupant_28, occupant_29 as occupant_29, occupant_30 as occupant_30 FROM cinema_sessions WHERE session_id = %s;", (cinema_session_id,))
    seat_and_occupant_data = cur.fetchone()

    dbClose(cur, conn)

    # Создадим список кортежей, содержащих номер места и его статус
    seats = [(f'seat_{i}', seat_and_occupant_data[i-1]) for i in range(1, 31)]

    occupants = seat_and_occupant_data[30:]

    return render_template('sessionDetails.html', session_data=session_data, seats=seats, occupants=occupants)


@app.route('/app/session/<int:cinema_session_id>/reserve', methods=['POST'])
def reserve_seats(cinema_session_id):
    if 'name' not in session:
        flash('Необходимо войти в систему для резервации мест', 'error')
        return redirect(url_for('loginPage'))

    selected_seats = request.form.getlist('selected_seats')

    if not selected_seats:
        flash('Выберите места для резервации', 'error')
        return redirect(url_for('session_details', cinema_session_id=cinema_session_id))

    conn = dbConnect()
    cur = conn.cursor()

    # Проверим статус каждого выбранного места
    for selected_seat in selected_seats:
        cur.execute(f"SELECT {selected_seat} FROM cinema_sessions WHERE session_id = %s;", (cinema_session_id,))
        seat_status = cur.fetchone()

        if seat_status and not seat_status[0]:
            # Место свободно, обновим его статус на "занято" и запишем имя пользователя
            username = session['name']
            seat_number = int(selected_seat.split('_')[-1])
            cur.execute(f"UPDATE cinema_sessions SET {selected_seat} = TRUE, occupant_{seat_number} = %s WHERE session_id = %s;", (username, cinema_session_id))
            conn.commit()
            flash(f'Место {selected_seat} успешно зарезервировано', 'success')
        else:
            # Место уже занято, обработаем это соответственно
            flash(f'Место {selected_seat} уже занято', 'error')

    dbClose(cur, conn)

    return redirect(url_for('session_details', cinema_session_id=cinema_session_id))
