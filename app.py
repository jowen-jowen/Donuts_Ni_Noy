from flask import Flask, render_template
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/shops')
def shops():
    return render_template('Shops.html')

@app.route('/products')
def products():
    return render_template('Products.html')

@app.route('/forgotPass')
def register():
    return render_template('ForgotPass.html')

@app.route('/login')
def login():
    return render_template('LogReg.html')

@app.route('/cart')
def cart():
    return render_template('Cart.html')


if __name__ == '__main__':
    app.run(debug=True)
