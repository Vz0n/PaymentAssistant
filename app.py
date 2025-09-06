from flask import Flask, render_template, session, redirect
from blueprints import admin, payment, account
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError

app = Flask(__name__)

# Don't keep templates stuff whitespaces
app.jinja_options["trim_blocks"] = True 
app.jinja_options["lstrip_blocks"] = True 

# Setup Extensions
CSRFProtect(app)

# Add Blueprints 
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(payment, url_prefix="/payment")
app.register_blueprint(account, url_prefix="/account")

@app.template_global()
def get_session_data(key: str):
    return session.get(key, "")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404

@app.errorhandler(405)
def not_allowed(_):
    return redirect("/", 302)

@app.errorhandler(500)
def generic_err(_):
    return render_template("error.html", message="""Ha ocurrido un error interno al intentar cargar la página o procesar tus datos.
    Si esto sigue ocurriendo, contacta a los administradores de la página."""), 500

@app.errorhandler(CSRFError)
def invalid_token_err(_):
    return render_template("error.html", 
            message="Tu petición contiene un token de verificación expirado. Recarga la página."), 400