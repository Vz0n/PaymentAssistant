from flask.blueprints import Blueprint
from flask import render_template, request, redirect, flash, get_flashed_messages, session
from flask import current_app as app
from puremagic import from_string, PureError
from json import loads
from database import Database
from utils import generate_token, Mailer, match_regex

from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from math import ceil

import requests

payment = Blueprint("payment", __name__)

# A mapping for the payment method and it's type name
METHODS = {
    "manual": "manual",
    "mercantil": "card",
}

@payment.before_request
def before():
    if not "role" in session:
        return redirect("/", 302)

@payment.get("/")
def index():
    db = Database()
    pending_fees = db.execute_query("SELECT pending_fees FROM users WHERE id=?", session["id"])[0][0]
    db.close()

    try:
        # We use the pydolarve API to get the dolar exchange rate
        json = requests.get("https://pydolarve.org/api/v1/dollar?page=bcv", timeout=5).json()
        exchange_rate = float(json["monitors"]["usd"]["price"])

        bs_price = ceil(float(app.assistant_config.get("fee_price")) * exchange_rate)

        return render_template("payment/index.html", fee_price=bs_price, 
                 user_fees=loads(pending_fees), exchange_rate=exchange_rate)
    except:
        return render_template("payment/index.html", 
                 user_fees=loads(pending_fees), fee_price=app.assistant_config.get("fee_price"))

@payment.post("/init")
def init():
    method = request.form.get("method", "")
    fee_number = request.form.get("fee_number", "")
    db = Database()

    pending_fees = loads(db.execute_query("SELECT pending_fees FROM users WHERE id=?", session.get("id"))[0][0])
    sent_manual = db.execute_query("SELECT id FROM verif_pending_payments WHERE user=?", session.get("id"))
    db.close()

    if not match_regex(fee_number, r"[0-9]") or not match_regex(method, r"[a-z]"):
        flash("Introduce un método de pago y cuota válida.")
        return redirect("error", 302)
    
    if int(fee_number) not in pending_fees:
        flash("Has introducido una cuota que no debes.")
        return redirect("error", 302)
    
    if len(sent_manual) > 0:
        flash("Tienes un pago pendiente por verificar. No puedes interactuar con esta sección hasta que se verifique tu pago.")
        return redirect("error", 302)

    ptype = METHODS.get(method)

    if not ptype:
        flash("Has introducido un método de pago desconocido.")
        return render_template("error", 302)
    
    session["payment_info"] = [ptype, fee_number]
    return render_template(f"payment/types/{ptype}.html", method=method.capitalize(), type=ptype)       

# This is where you should implement the automatic payment processing logic for bank's card payment.
@payment.post("/do/card")
def mercantil():
    payment_info = session.get("payment_info")

    if not payment_info: return redirect("/payment", 302)

    payment_info.append("done")
    session["payment_info"] = payment_info
    
    return redirect("/payment/success", 303)

@payment.post("/do/manual")
def manual():
    sid = session.get("id")
    payment_info = session.get("payment_info")

    if not payment_info: return redirect("/payment", 302)

    ci = request.form.get("ci", "")
    payment_id = request.form.get("payment_id", "")
    attachment = request.files.get("check_file", "")
    error = False

    if ci == "" or payment_id == "":
        flash("Debes rellenar todos los campos")
        error = True

    if len(ci) > 8 or not match_regex(ci, r"[0-9]{6,7}"):
        flash("Introduce una cédula de identidad válida.")
        error = True

    try:
        raw_data = attachment.stream.read()
        mimetype = from_string(raw_data, mime=True)

        if mimetype.find("pdf") == -1 and mimetype.find("image") == -1:
            raise PureError

    except PureError:
        flash("Debes subir una imagen o archivo PDF válido.")
        error = True

    mailer = Mailer()

    if mailer.server == None:
        flash("Parece que la aplicación no puede enviar correos. Contacte a un administrador para obtener ayuda.")
        error = True

    if error:
        return redirect("/payment/error", 302)
    
    text = MIMEText(render_template("email/forward.html", ci=ci, email=session.get("email"), 
                    pid=payment_id, fname=session.get("fname"), lname=session.get("lname"), 
                    fee_number=payment_info[1]), "html")

    if mimetype == "application/pdf":
        email_attachment = MIMEApplication(raw_data, "pdf")
    else:
        email_attachment = MIMEImage(raw_data)

    email = MIMEMultipart(_subparts=[text, email_attachment])
    email.add_header("Subject", f"Recibo de pago para la cuota {payment_info[1]} por parte de C.I {ci}")
    email.add_header("From", app.config["FROM_EMAIL"])
    email.add_header("To", app.assistant_config.get("forward_email"))

    mailer.send_mail(email)

    db = Database()
    db.execute_update("INSERT INTO verif_pending_payments VALUES (?, ?, ?, ?, ?)", generate_token(16), 
                      sid, payment_info[1], payment_id, ci)
    db.close()

    payment_info.append("done")
    session["payment_info"] = payment_info

    return redirect("/payment/success", 303)

@payment.route("/cancel")
def cancel():
    session.pop("payment_info")

    return redirect("/payment", 301)

@payment.route("/success")
def success():
    payment_info: list[str] = session.get("payment_info", [])

    if len(payment_info) < 3:
        return redirect("/payment/", 302)

    session.pop("payment_info")

    return render_template("payment/success.html", method=payment_info[0])

@payment.route("/error")
def error():
    return render_template("payment/error.html", messages=get_flashed_messages())