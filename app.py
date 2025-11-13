import random  # ✅ use correct module for randint
import smtplib
from email.mime.text import MIMEText

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "Css@12345"

# --- Database connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Css@12345",  #MySQL password
        database="donut_db"
    )

import os
from werkzeug.utils import secure_filename
# where the uploaded pictures are stored
UPLOAD_FOLDER = 'static/uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# remove/replace the possible invalid characters to be inputted in database
def sanitize_table_name(name):

    table_name = name.lower()
    table_name = table_name.replace(" ", "_")
    table_name = table_name.replace("'", "")
    table_name = table_name.replace('"', '')
    table_name = table_name.replace("-", "_")
    return table_name


#----------------------------------------------------------------------------------------------------------------------- upload_shops Route = Shops Image Upload
# Upload new shop and create dynamic table for its products
# -----------------------------------
@app.route('/upload_shops', methods=['POST'])
def upload_shops():
    shop_name = request.form['shop_name']
    file_shop = request.files.getlist('shop_images')

    if not file_shop:
        return "No file selected", 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Save shop image(s) into shops table
        for fileshop in file_shop:
            if fileshop and allowed_file(fileshop.filename):
                filename = secure_filename(fileshop.filename)
                fileshop.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    "INSERT INTO shops (name, shop_img) VALUES (%s, %s)",
                    (shop_name, filename)
                )

        # Create a new table for this shop's products dynamically
        table_name = sanitize_table_name(shop_name)  # safe table name
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                product_img VARCHAR(255) NOT NULL
            )
        """
        cursor.execute(create_table_query)

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin'))

    except Exception as e:
        return f"Upload failed: {e}"



#----------------------------------------------------------------------------------------------------------------------- upload_img Route = Product Image Upload
# Upload product to selected shop table

@app.route('/upload_img', methods=['POST'])
def upload_img():
    image_name = request.form['image_name']
    shop_table = request.form['shop_table']  # selected shop table
    price = request.form['price']
    files = request.files.getlist('images')

    if not files:
        return "No files selected", 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Sanitize table name before using it in query
        shop_table = sanitize_table_name(shop_table)

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

                # Insert into shop-specific table
                cursor.execute(
                    f"INSERT INTO `{shop_table}` (name, price, product_img) VALUES (%s, %s, %s)",
                    (image_name, price, filename)
                )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('admin'))

    except Exception as e:
        return f"Upload failed: {e}"



# ---------------------------------------------------------------------------------------------------------------------- remove_product Route
# Remove product from a shop-specific table

@app.route('/remove_product/<shop_table>/<product_name>', methods=['POST'])
def remove_product(shop_table, product_name):
    shop_table = sanitize_table_name(shop_table)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM `{shop_table}` WHERE name = %s", (product_name,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------------------------- home Route
@app.route('/')
def home():
    return render_template('Home.html')

#----------------------------------------------------------------------------------------------------------------------- about Route

@app.route('/about')
def about():
    return render_template('About.html')

#----------------------------------------------------------------------------------------------------------------------- cart Route

@app.route('/cart')
def cart():
    return render_template('Cart.html')


#----------------------------------------------------------------------------------------------------------------------- shops Route = Retrieving Images from shop table to Shop Page
# Remove shop in the database

@app.route('/remove_shop/<shop_name>', methods=['POST'])
def remove_shop(shop_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete shop from shops table
    cursor.execute("DELETE FROM shops WHERE name = %s", (shop_name,))

    # Drop shop's product table safely
    table_name = sanitize_table_name(shop_name)
    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin'))

# for retrieving the images from shops table into the Shops Page
@app.route('/shops')
def shops():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM shops")
    shops_com = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('Shops.html', shops=shops_com)



#----------------------------------------------------------------------------------------------------------------------- admin Route = retrieval and testing if the files are uploaded
# for retrieving and testing if the images are being uploaded
# fetching data from database

def fetch_all(query):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.route('/admin')
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetching all shops
    cursor.execute("SELECT * FROM shops")
    shops_com = cursor.fetchall()

    # Fetching products for each shop
    products_by_shop = {}
    for shop in shops_com:
        table_name = sanitize_table_name(shop['name'])
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        if cursor.fetchone():
            cursor.execute(f"SELECT * FROM `{table_name}`")
            products_by_shop[shop['name']] = cursor.fetchall()
        else:
            products_by_shop[shop['name']] = []

    cursor.close()
    conn.close()

    return render_template('Admin.html', shops=shops_com, products_by_shop=products_by_shop)


#----------------------------------------------------------------------------------------------------------------------- logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#----------------------------------------------------------------------------------------------------------------------- register Route = Register (with OTP)
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
            return f" Error sending email: {str(e)}"

    return render_template('LogReg.html')

#----------------------------------------------------------------------------------------------------------------------- verify_otp Route = Verifying the OTP and holding the name,email,password
#-----------------------------------------------------------------------------------------------------------------------                    until the OTP is correct

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

#----------------------------------------------------------------------------------------------------------------------- login Route = Retrieval of email/password and comparing the hashed password
#-----------------------------------------------------------------------------------------------------------------------               into the real password
# retrieving the email and password and comparing if the hashed password is the same to the unhashed password
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

#----------------------------------------------------------------------------------------------------------------------- logged Route = For Checking if the user got logged in
# if the user is successfully logged it will go to the success Page
@app.route('/logged')
def logged():
    name = session.get('name', 'Guest')
    return render_template('Home.html', name=name)

@app.route('/dunkin')
def dunkin():
    return render_template('Dunkin.html')

if __name__ == '__main__':
    app.run(debug=True)
