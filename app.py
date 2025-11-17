import random  # ✅ use correct module for randint
import smtplib
from email.mime.text import MIMEText

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
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

#----------------------------------------------------------------------------------------------------------------------- home Route = Landing Page
@app.route('/')
def home():
    return render_template('Home.html')

#----------------------------------------------------------------------------------------------------------------------- contact Route
@app.route('/contact')
def contact():
    return render_template('Contact.html')


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
            # Insert into pending_users instead
            cursor.execute("INSERT INTO pending_users (name, email, password) VALUES (%s, %s, %s)",
                           (name, email, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()

            # Clear session data
            for key in ['pending_name', 'pending_email', 'pending_password', 'otp']:
                session.pop(key, None)

            return jsonify({"success": True})

        except Exception as e:
            return f"Database error: {e}"
    else:
        return render_template("OTPVerif.html",
                               error="Invalid OTP. Please try again.",
                               email=session.get('pending_email'))



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
            conn.close()

        except Error:
            flash("Database error! Try again later.", "error")
            return redirect(url_for('login'))

        if user and check_password_hash(user['password'], password):
            session['name'] = user['name']
            session['user_id'] = user['id']
            session['user_type'] = user.get("user_type", "user")

            if session['user_type'] == "admin":
                return redirect(url_for('admin'))
            return redirect(url_for('logged'))

        # If login fails it will show error message
        error = "Email or Password is incorrect"
        return render_template('LogReg.html', login_error=error)

    return render_template('LogReg.html', error="Email or Password is incorrect")

#----------------------------------------------------------------------------------------------------------------------- logged Route = For Checking if the user got logged in
# if the user is successfully logged it will go to the success Page
@app.route('/logged')
def logged():
    name = session.get('name', 'Guest')
    return render_template('Home.html', name=name)


#----------------------------------------------------------------------------------------------------------------------- forgot_pass Route
# Forgot Password
@app.route('/forgot_pass', methods=['GET', 'POST'])
def forgot_pass():
    if request.method == 'POST':
        email = request.form['email'].strip()

        # check if email exists in DB
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return render_template('ForgotPass.html',
                error="Email not found")

        # store email temporarily
        session['reset_email'] = email

        # generate OTP
        otp = random.randint(100000, 999999)
        session['reset_otp'] = str(otp)

        # send OTP email
        try:
            sender = "japquinones1977@gmail.com"
            app_password = "vtwk zbdv ulxe bzpm"

            msg = MIMEText(f"Your password reset OTP is: {otp}")
            msg['Subject'] = "Password Reset OTP"
            msg['From'] = "Dunkin Ni Noy"
            msg['To'] = email

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, app_password)
                server.sendmail(sender, email, msg.as_string())

            return render_template("OTPForgot.html", email=email)

        except Exception as e:
            return f"Error sending email: {e}"

    return render_template('ForgotPass.html')

#----------------------------------------------------------------------------------------------------------------------- verify_forgot_otp Route
@app.route('/verify_forgot_otp', methods=['POST'])
def verify_forgot_otp():
    entered_otp = request.form['otp'].strip()

    if entered_otp == session.get('reset_otp'):
        return render_template('ResetPass.html')
    else:
        return render_template('OTPForgot.html', error="Invalid OTP. Please try again.",
                               email=session.get('reset_email'))

#----------------------------------------------------------------------------------------------------------------------- reset_password Route
@app.route('/reset_password', methods=['POST'])
def reset_password():
    new_password = request.form['new_password'].strip()
    email = session.get('reset_email')

    hashed_password = generate_password_hash(new_password)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=%s WHERE email=%s",
                   (hashed_password, email))
    conn.commit()
    cursor.close()
    conn.close()

    # clear temporary session data
    for key in ['reset_email', 'reset_otp']:
        session.pop(key, None)

    return redirect(url_for('login'))

#----------------------------------------------------------------------------------------------------------------------- shops Route = Retrieving Images from shop table to Shop Page
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

#----------------------------------------------------------------------------------------------------------------------- shop_products Route

@app.route('/shops/<shop_name>')
def shop_products(shop_name):
    table_name = sanitize_table_name(shop_name)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch products of the selected shop
    cursor.execute(f"SELECT * FROM `{table_name}`")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('Shops.html', products=products, shop_name=shop_name)

#----------------------------------------------------------------------------------------------------------------------- cart Route

@app.route("/cart")
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM cart WHERE user_id=%s", (session['user_id'],))
    cart_rows = cursor.fetchall()

    cart_items = []
    total_price = 0

    for row in cart_rows:
        table = sanitize_table_name(row['shop_table'])
        product_id = row['product_id']

        # Get product info from the shop-specific table
        cursor.execute(f"SELECT name, price, product_img FROM `{table}` WHERE id=%s", (product_id,))
        product = cursor.fetchone()

        if product:
            subtotal = product['price'] * row['quantity']
            total_price += subtotal
            cart_items.append({
                "product_name": product['name'],
                "price": product['price'],
                "product_img": product['product_img'],
                "quantity": row['quantity'],

                # REAL numeric product ID
                "product_id": row['product_id'],
                "shop_table": row["shop_table"],


                # UNIQUE KEY for HTML (product name + shop)
                "unique_id": f"{product['name']}_{row['shop_table']}".replace(" ", "_")
            })

    cursor.close()
    conn.close()

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

#----------------------------------------------------------------------------------------------------------------------- add_to_cart Route
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = request.form.get("product_id")
    shop_table = request.form.get("shop_table")
    quantity = int(request.form.get("quantity"))

    if not product_id or not shop_table:
        return "Missing product or shop information", 400

    shop_table = sanitize_table_name(shop_table)
    user_name = session.get('name', 'Guest')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if item already exists in cart for this user + shop
    cursor.execute(
        "SELECT * FROM cart WHERE user_id=%s AND product_id=%s AND shop_table=%s",
        (session['user_id'], product_id, shop_table)
    )
    existing = cursor.fetchone()

    if existing:
        # Update quantity
        cursor.execute(
            "UPDATE cart SET quantity = quantity + %s WHERE cart_id=%s",
            (quantity, existing['cart_id'])
        )
    else:
        # Insert new cart item
        cursor.execute(
            "INSERT INTO cart (user_id, name, product_id, shop_table, quantity) VALUES (%s, %s, %s, %s ,%s)",
            (session['user_id'], user_name, product_id, shop_table, quantity)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Product added to cart!"})

#----------------------------------------------------------------------------------------------------------------------- update_quantity Route =
@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    product_id = request.form['product_id']
    action = request.form['action']

    if action == "increase":
        cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE user_id=%s AND product_id=%s",
                       (session['user_id'], product_id))
    else:
        cursor.execute("UPDATE cart SET quantity = GREATEST(quantity - 1, 1) WHERE user_id=%s AND product_id=%s",
                       (session['user_id'], product_id))

    conn.commit()
    return redirect(url_for('cart'))

#----------------------------------------------------------------------------------------------------------------------- remove_cart_item Route
@app.route('/remove_cart_item', methods=['POST'])
def remove_cart_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = request.form['product_id']
    shop_table = request.form['shop_table']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id=%s AND product_id=%s AND shop_table=%s",
                   (session['user_id'], product_id, shop_table))
    conn.commit()

    return jsonify({"success": True, "message": "Item removed!"})

#----------------------------------------------------------------------------------------------------------------------- checkout Route
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('Checkout.html')

#----------------------------------------------------------------------------------------------------------------------- confirm_order Route
@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    # this confirms if the user is not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    fullname = request.form['fullname']
    phone = request.form['phone']
    address = request.form['address']
    payment = request.form['payment']
    notes = request.form.get('notes', '')

    user_id = session['user_id']
    username = session['name']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all items from cart
    cursor.execute("SELECT * FROM cart WHERE user_id=%s", (user_id,))
    cart_items = cursor.fetchall()

# if there's nothing in cart it will return the text
    if not cart_items:
        return "Cart is empty"

    products_list = []
    total_price = 0

    for item in cart_items:
        table = sanitize_table_name(item['shop_table'])

        cursor.execute(
            f"SELECT name, price FROM `{table}` WHERE id = %s",
            (item['product_id'],)
        )
        product = cursor.fetchone()

        if product:
            subtotal = product['price'] * item['quantity']
            total_price += subtotal
            products_list.append(
                f"{product['name']} (Qty: {item['quantity']})"
            )

    products_text = ", ".join(products_list)

    # Inserting order into DB
    cursor.execute("""
        INSERT INTO orders (user_id, username, products, total_price, fullname, phone, address, payment_method, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user_id, username, products_text, total_price,fullname, phone, address, payment, notes))

    # Clear cart
    cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True, "message": "Order Confirmed"})

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

    # Fetch shops
    cursor.execute("SELECT * FROM shops")
    shops_com = cursor.fetchall()

    # Fetch all users
    cursor.execute("SELECT id, name, email, user_type, created_at FROM users")
    users = cursor.fetchall()

    # Fetch pending users
    cursor.execute("SELECT id, name, email, created_at FROM pending_users")
    pending_users = cursor.fetchall()

    # Fetch products for each shop
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

    return render_template('Admin.html', shops=shops_com, products_by_shop=products_by_shop,
                           users=users, pending_users=pending_users)

#----------------------------------------------------------------------------------------------------------------------- remove_user Route = Removing the user
@app.route('/remove_user/<int:user_id>', methods=['POST'])
def remove_user(user_id):

    # Prevent auto-delete of currently logged-in admin
    if 'user_id' in session and session['user_id'] == user_id:
        flash("You cannot delete your own account while logged in as admin!")
        return redirect(url_for('admin'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check user type BEFORE deleting
        cursor.execute("SELECT user_type FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user and user[0] == "admin":
            flash("You cannot delete another admin.")
            conn.close()
            return redirect(url_for('admin'))

        # Proceed with delete
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        cursor.close()
        conn.close()

        flash("User removed successfully!")
    except Exception as e:
        flash(f"Error deleting user: {e}")

    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------------------------- promote_user Route = Promote User to Admin
@app.route('/promote_user/<int:user_id>', methods=['POST'])
def promote_user(user_id):
    try:
        # Prevent promoting an already admin
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_type FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if not user or user[0] == 'admin':
            conn.close()
            flash("Cannot promote this user.", "error")
            return redirect(url_for('admin'))

        cursor.execute("UPDATE users SET user_type='admin' WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("User promoted to admin successfully!", "success")
    except Exception as e:
        flash(f"Error promoting user: {e}", "error")
    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------------------------- demote_user Route = Demote admin from admin to user

@app.route('/demote_user/<int:user_id>', methods=['POST'])
def demote_user(user_id):
    try:
        if 'user_id' in session and session['user_id'] == user_id:
            flash("You cannot demote yourself!", "error")
            return redirect(url_for('admin'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_type FROM users WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if not user or user['user_type'].lower() != 'admin':
            conn.close()
            flash("Cannot demote this account.", "error")
            return redirect(url_for('admin'))

        #if success the user_type "admin" will be "user"
        cursor.execute("UPDATE users SET user_type='user' WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Admin demoted to user successfully!", "success")
    except Exception as e:
        flash(f"Error demoting admin: {e}", "error")
    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------------------------- approve_user Route = Approved user will be moved to 'Registered user' table

@app.route('/approve_user/<int:user_id>', methods=['POST'])
def approve_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get user info from pending_users
        cursor.execute("SELECT name, email, password FROM pending_users WHERE id=%s", (user_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            flash("User not found", "error")
            return redirect(url_for('admin'))

        # Insert into users table
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (user['name'], user['email'], user['password']))

        # Remove from pending_users
        cursor.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        flash("User approved successfully!", "success")
    except Exception as e:
        flash(f"Error approving user: {e}", "error")
    return redirect(url_for('admin'))

#----------------------------------------------------------------------------------------------------------------------- remove_pending_user Route = Remove pending user

@app.route('/remove_pending_user/<int:user_id>', methods=['POST'])
def remove_pending_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pending_users WHERE id=%s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Pending user removed", "success")
    except Exception as e:
        flash(f"Error removing pending user: {e}", "error")
    return redirect(url_for('admin'))




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

        # Save shop images into shops table
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

#----------------------------------------------------------------------------------------------------------------------- remove_shops Route
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

        # Sanitize(remove un-necessary character ex: ',") table name before using it in query
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



# ---------------------------------------------------------------------------------------------------------------------- remove_product Route = Remove product to specific Shop

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


#----------------------------------------------------------------------------------------------------------------------- logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
