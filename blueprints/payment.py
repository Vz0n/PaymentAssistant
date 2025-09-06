from flask.blueprints import Blueprint
from flask import render_template, request, redirect, flash, get_flashed_messages, session
from flask import current_app as app
from puremagic import from_string, PureError
from json import loads
from database import Database
from utils import generate_token, match_regex, write_data_to_storage

from math import ceil

import requests

payment = Blueprint("payment", __name__)

# A mapping for the payment method and it's type name
METHODS = {
    "manual": "manual"
}

@payment.before_request
def before():
    if "id" not in session:
        return redirect("/account/login", 303)

    # We won't allow requests sent from a client like cURL to those endpoints
    if request.path.startswith("/do/") and not session.get("payment_id", None):
        return redirect("/payment", 302)

@payment.get("/")
def index():
    db = Database()
    pending_fees = db.execute_query("SELECT pending_fees FROM users WHERE id = ?", session["id"])[0][0]
    db.close()

    ctx = {"user_fees": loads(pending_fees), "messages": get_flashed_messages(True)}
    config_price = app.assistant_config.get("fee_price")

    try:
        # We use the pydolarve API to get the dolar exchange rate
        json = requests.get("https://pydolarve.org/api/v1/dollar?page=bcv", timeout=5).json()
        exchange_rate = float(json["monitors"]["usd"]["price"])

        bs_price = ceil(float(config_price) * exchange_rate)
        ctx["fee_price"] = bs_price
        ctx["exchange_rate"] = exchange_rate
    except:
        ctx["fee_price"] = config_price

    return render_template("payment/index.html", **ctx)

@payment.post("/init")
def init():
    method = request.form.get("method", "")
    fee_number = request.form.get("fee_number", "")
    db = Database()
    message = None

    sent_manual = db.execute_query("SELECT id FROM verif_pending_payments WHERE user = ?", session.get("id"))
    db.close()

    if not match_regex(fee_number, r"^[0-9]{1,2}$"):
        message = ("Número de cuota inválido.", "error")
    
    if len(sent_manual) > 0:
        message = ("Tienes un pago pendiente por verificar. No podrás interactuar con esta sección hasta que se verifique tu pago.", "error")

    ptype = METHODS.get(method, "manual")

    if not ptype:
        message = ("Método de pago desconocido.", "error")
    
    if message:
        flash(*message)
        return redirect("/payment", 302)
    
    # Token to ensure that the payment endpoints will be accesed from the website
    # and to give the payment an unique identification 
    session["payment_id"] = generate_token(24)

    return render_template(f"payment/types/{ptype}.html", method=method.capitalize(), 
                           fee_number=fee_number)

@payment.post("/do/manual")
def manual():
    user_id = session.get("id")
    
    fee_number = request.form.get("fee_number", "")
    ci = request.form.get("ci", "")
    attachment = request.files.get("check_file", "")

    if not match_regex(fee_number, r"^[0-9]{1,2}$"):
        flash("Número de cuota inválido", "error")

    if not match_regex(ci, r"^[0-9]{7,8}$"):
        flash("Introduce una cédula de identidad válida.", "error")

    try:
        if attachment == "": raise PureError

        raw_data = attachment.stream.read()
        mimetype = from_string(raw_data, mime=True)

        if mimetype != "application/pdf" and mimetype.find("image") == -1:
            raise PureError
        
        extension = from_string(raw_data)
    except PureError:
        flash("Debes subir una imagen o archivo PDF válido.", "error")

    messages = get_flashed_messages(True)

    if len(messages) > 0:
        return render_template("payment/types/manual.html", 
                               messages=messages, fee_number=fee_number)
    
    payment_id = session.pop("payment_id")
    filename = f"payment_{payment_id}{extension}"

    # Move the uploaded file to the storage
    write_data_to_storage(raw_data, filename)

    db = Database()
    db.execute_update("INSERT INTO verif_pending_payments VALUES (?, ?, ?, ?, ?)", payment_id, 
                      user_id, fee_number, ci, filename)
    db.close()

    return redirect("/payment/success", 303)

@payment.route("/cancel")
def cancel():
    # Remove the token
    session.pop("payment_id")

    return redirect("/payment", 301)

@payment.route("/success")
def success():
    return render_template("payment/success.html")