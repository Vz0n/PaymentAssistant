from flask import render_template, request, session, redirect, flash, get_flashed_messages, send_from_directory
from flask import current_app as app
from flask.blueprints import Blueprint
from json import loads, dumps
from os import unlink

from utils import match_regex, get_valid_dates, Mailer
from database import Database

admin = Blueprint("admin", __name__)

@admin.before_request
def check_admin():
    if not session.get("role", "") == "admin":
        return redirect("/", 302)

@admin.get("/")
def index():
    return render_template("admin/index.html", session=session)

@admin.get("/users")
def users():
    query_string = request.query_string.decode(errors="ignore").split("=")
    db = Database()  

    # Handle cases where the "page" parameter can not be present and so
    try:
        index = query_string.index("page")
        page = query_string[index + 1] if len(query_string) > 1 else 0
    except ValueError:
        page = 0
     
    users_set = db.execute_query("SELECT email,fname,sname,role FROM users LIMIT ?,?", 8*page, (page + 1)*8)

    return render_template("admin/users.html", session=session, users=users_set, page=page + 1)

@admin.get("/payments")
def payments():
     query_string = request.query_string.decode(errors="ignore").split("=")
     db = Database()

     try:
        index = query_string.index("page")
        page = query_string[index + 1] if len(query_string) > 1 else 0
     except ValueError:
        page = 0

     pending_payments = db.execute_query("SELECT id,user,ci,fee_number FROM verif_pending_payments LIMIT ?,?", page*8, (page + 1)*8)
     db.close()

     return render_template("admin/payments.html", payments=pending_payments, page=page + 1,
                            message=get_flashed_messages())

@admin.get("/payments/view/<payment_id>")
def view_payment(payment_id: str):
    if not match_regex(payment_id, r"^[a-zA-Z0-9]{24}$"):
          return redirect("/admin/", 302)
    
    db = Database()
    user_payment = db.execute_query("SELECT ci,fee_number,filename,user FROM verif_pending_payments WHERE id = ?", payment_id)
    user_id = user_payment[0][3] if len(user_payment) > 0 else -1

    user_names = db.execute_query("SELECT fname,sname FROM users WHERE id = ?", user_id)
    db.close()

    if len(user_names) != 1:
         return render_template("admin/view_payment.html", 
                                message="El pago al que intentas acceder no existe.")
    
    return render_template("admin/view_payment.html", payment_data=user_payment[0],
                    user_fname=user_names[0][0], user_sname=user_names[0][1], id=payment_id)

@admin.route("/storage/<filename>")
def storage_handler(filename: str):
    return send_from_directory("storage/", filename)

@admin.post("/payments/<action>")
def set_payment(action: str):
     pid = request.form.get("payment_id", "")
     reason = request.form.get("reason", "")

     if not match_regex(pid, r"^[a-zA-Z0-9]{24}$"):
          return "ID de pago inválida.", 400
    
     db = Database()
     payment_data = db.execute_query("SELECT user,fee_number,filename FROM verif_pending_payments WHERE id = ?", pid)

     if len(payment_data) < 1:
          db.close()
          return "El pago al que haces referencia no existe.", 400

     user_data = db.execute_query("SELECT pending_fees,fname,sname,email FROM users WHERE id = ?", 
                                  payment_data[0][0])
    
     if action == "accept": 
        fees: list[int] = loads(user_data[0][0])
        fees.remove(payment_data[0][1])
        db.execute_update("UPDATE users SET pending_fees = json(?)", dumps(fees))

        mail_subject = "Pago aceptado"
        flash("El pago ha sido marcado como aceptado.")
     elif action == "reject":
        if reason == "":
             return "Debes dar una razón por la cual el pago está siendo rechazado.", 400
        
        mail_subject = "Pago rechazado"
        flash("El pago ha sido marcado como rechazado.")
     else:
        db.close()
        return "Acción inválida.", 400
     
     template_ctx = {"username": f"{user_data[0][1]} {user_data[0][2]}", "reason": reason, 
                     "payment_id": pid}
     mailer = Mailer()

     # reject - ed,  accept - ed
     text = render_template(f"email/payment_{action}ed.html", **template_ctx)
     attachment_file = payment_data[0][2]
     email = user_data[0][3]
        
     if not mailer.send_html_mail(text, app.config["FROM_EMAIL"], email, mail_subject):
            app.logger.error(f"error sending mail to {email}; is the smtp server up?")
    
     db.execute_update("DELETE FROM verif_pending_payments WHERE id = ?", pid)
     db.close()

     # Lastly, delete the payment's attachment
     unlink(f"storage/{attachment_file}")

     return "", 204

@admin.get("/settings")
def settings():
    data = [
         app.assistant_config.get("forward_email"),
         app.assistant_config.get("fee_price"),
         app.assistant_config.get("fee_dates")
    ]

    return render_template("admin/settings.html", session=session, data=data)

@admin.post("/settings/edit")
def settings_edit():
     new_dates = request.form.get("dates", "").split("|")
     new_email = request.form.get("receipt_email", "")
     new_price = request.form.get("fee_price", "")
     message = None

     if not match_regex(new_email, r"\w+@\w+(?:\.\w+)+$"):
            message = ("Introduce un email válido.", 400)

     if get_valid_dates(new_dates) != 5:
            message = ("Introduce fechas válidas para el pago de las cuotas.", 400)

     if not match_regex(new_price, r"^[0-9]+$"):
            message = ("Introduce un precio válido para las cuotas.", 400)
        
     if not message:
            # This may seem pretty weird, but for security reasons 
            # we just allow the user to edit these values from the webserver
            values = {
                 "fee_dates": new_dates,
                 "forward_email": new_email,
                 "fee_price": new_price
            }

            for k in values:
                app.assistant_config.set(k, values[k])

            app.assistant_config.save()
            message = "Datos actualizados con éxito. Debe reiniciar la aplicación para que los cambios tengan efecto en las tareas automáticas."
        
     return message