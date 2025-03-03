from flask import Flask, render_template, session, redirect
from blueprints import admin, payment, account
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError

app = Flask(__name__)

# Setup Extensions
CSRFProtect(app)

# Add Blueprints 
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(payment, url_prefix="/payment")
app.register_blueprint(account, url_prefix="/account")

@app.route("/")
def index():
    return render_template("index.html", session=session)

@app.route("/about")
def about():
    return render_template("about.html", session=session)

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html", session=session), 404

@app.errorhandler(405)
def not_allowed(_):
    return redirect("/", 302)

@app.errorhandler(500)
def generic_err(_):
    return render_template("50x.html", session=session, message="Ha ocurrido un error extraño"), 500

@app.errorhandler(CSRFError)
def invalid_token_err(_):
    return "Tu petición contiene un token CSRF inválido. Intenta enviarla de nuevo", 400