from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "Css@12345"

# Database conn
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Css@12345",  # password
        database="donut_db"
    )

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/cart')
def cart():
    return render_template('Cart.html')

@app.route('/shops')
def shops():
    return render_template('Shops.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # Hash password using Werkzeug (PBKDF2-SHA256)
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("REGISTER ERROR:", e)

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
        except Error:
            return redirect(url_for('login'))

        if user:
            if check_password_hash(user['password'], password):
                session['name'] = user['name']
                session['user_type'] = user.get('user_type', 'user')  # default to user


                if user['user_type'] == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('logged'))
            else:
                # wrong password
                return redirect(url_for('login'))
        else:
            # mo user
            return redirect(url_for('login'))

    return render_template('LogReg.html')


# login success
@app.route('/logged')
def logged():
    name = session.get('name', 'Guest')
    return render_template('Success.html', name=name)

# logout
@app.route('/logout')
def logout():
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    return render_template('Admin.html')

if __name__ == '__main__':
    app.run(debug=True)


