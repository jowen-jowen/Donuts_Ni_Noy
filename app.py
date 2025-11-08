import smtplib
from email.mime.text import MIMEText
import random  # ✅ use correct module for randint

from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "Css@12345"

# --- Database connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Css@12345",  # your MySQL password
        database="donut_db"
    )

# --- ROUTES ---

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

@app.route('/admin')
def admin():
    return render_template('Admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Register (with OTP)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # temporarily store in session
        session['pending_name'] = name
        session['pending_email'] = email
        session['pending_password'] = password

        # generate OTP
        otp = random.randint(100000, 999999)
        session['otp'] = str(otp)

        # send OTP email
        try:
            sender = "japquinones1977@gmail.com"
            app_password = "vtwk zbdv ulxe bzpm"  # Gmail app password
            msg = MIMEText(f"Your OTP code is: {otp}")
            msg['Subject'] = "Your OTP Verification Code"
            msg['From'] = sender
            msg['To'] = email

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, app_password)
                server.sendmail(sender, email, msg.as_string())

            return render_template("OTPVerif.html", email=email)

        except Exception as e:
            return f"❌ Error sending email: {str(e)}"

    return render_template('LogReg.html')

# for verification of OTP
@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    entered_otp = request.form['otp'].strip()

    if entered_otp == session.get('otp'):
        name = session.get('pending_name')
        email = session.get('pending_email')
        password = session.get('pending_password')

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()

            # clear session data
            for key in ['pending_name', 'pending_email', 'pending_password', 'otp']:
                session.pop(key, None)

            return redirect(url_for('login'))

        except Exception as e:
            return f"Database error: {e}"
    else:
        return render_template("OTPVerif.html",
            error="Invalid OTP. Please try again.",
            email=session.get('pending_email')
        )

# --- STEP 3: Login ---
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
                user_type = user.get('user_type', 'user')

                # redirect based on user_type
                if user_type == 'admin':
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('logged'))
            else:
                return render_template('LogReg.html', error="Incorrect password")
        else:
            return render_template('LogReg.html', error="No user found")

    return render_template('LogReg.html')

# --- STEP 4: Logged user page ---
@app.route('/logged')
def logged():
    name = session.get('name', 'Guest')
    return render_template('Success.html', name=name)


if __name__ == '__main__':
    app.run(debug=True)
