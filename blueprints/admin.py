from flask import render_template, request, session, redirect, flash, get_flashed_messages
from flask import current_app as app
from flask.blueprints import Blueprint
from json import loads, dumps

from utils import match_regex, find_matches
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
     
    users_set = db.execute_query("SELECT email,fname,lname FROM users LIMIT ?,?", 8*page, (page + 1)*8)

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

     pending_payments = db.execute_query("SELECT id,user,fee_number,ci FROM verif_pending_payments LIMIT ?,?", page*8, (page + 1)*8)
     db.close()

     return render_template("admin/payments.html", payments=pending_payments, page=page + 1,
                            message=get_flashed_messages())

@admin.get("/payments/view/<payment_id>")
def view_payment(payment_id: str):
    if not match_regex(payment_id, r"[a-zA-Z0-9]"):
          return redirect("/admin/", 302)
    
    db = Database()
    user_payment = db.execute_query("SELECT ci,transaction_id,fee_number,user FROM verif_pending_payments WHERE id=?", payment_id)
    user_id = user_payment[0][3] if len(user_payment) > 0 else -1

    user_names = db.execute_query("SELECT fname,lname FROM users WHERE id=?", user_id)
    db.close()

    if len(user_payment) < 1:
         return render_template("admin/view_payment.html", 
                                message="El pago al que intentas acceder no existe.")
    
    return render_template("admin/view_payment.html", payment_data=user_payment[0],
                           user_names=user_names[0], id=payment_id)

@admin.post("/payments/<action>")
def set_payment(action: str):
     pid = request.form.get("payment_id")

     if not match_regex(pid, r"[a-zA-Z0-9]"):
          return "Debes dar una ID de pago válida.", 400
    
     db = Database()
     result = db.execute_query("SELECT user,fee_number FROM verif_pending_payments WHERE id=?", pid)

     if len(result) < 1:
          db.close()
          return "El pago al que haces referencia fue eliminado.", 400
     
     user = result[0]
             
     if action == "accept":
        fees: list[int] = loads(db.execute_query("SELECT pending_fees FROM users WHERE id=?", user[0])[0][0])
        fees.remove(user[1])
        db.execute_update("UPDATE users SET pending_fees=json(?)", dumps(fees))

        flash("El pago ha sido aceptado.")
     elif action == "reject":
        flash("El pago ha sido rechazado.")
     else:
        db.close()
        return "", 400
          
     db.execute_update("DELETE FROM verif_pending_payments WHERE id=?", pid)
     db.close()

     return "/admin/payments", 303

@admin.get("/settings")
def settings():
    data = [
         app.assistant_config.get("fee_dates"),
         app.assistant_config.get("forward_email"),
         app.assistant_config.get("fee_price")
    ]

    return render_template("admin/settings.html", session=session, data=data)

@admin.post("/settings/edit")
def settings_edit():
     new_dates = request.form.get("dates", "")
     new_email = request.form.get("receipt_email", "")
     new_price = request.form.get("fee_price", "")
     message = None

     if not match_regex(new_email, r"\w+@\w+(?:\.\w+)+$"):
            message = ("Introduce un email válido.", 400)

     if len(new_dates.split("|")) != 5 or len(find_matches(new_dates, r"(([0-9]{4})-([0-9]{2})-([0-9]{2}))")) < 5:
            message = ("Introduce fechas válidas para el pago de las cuotas.", 400)

     if not match_regex(new_price, r"[0-9]"):
            message = ("Introduce un precio válido para las cuotas.", 400)
        
     if not message:
            # This may seem pretty weird, but for security reasons 
            # we just allow the user to edit these values from the webserver
            values = {
                 "fee_dates": new_dates.split("|"),
                 "forward_email": new_email,
                 "fee_price": new_price
            }

            for k in values:
                app.assistant_config.set(k, values[k])

            app.assistant_config.save()
            message = "Datos actualizados con éxito. Debe reiniciar la aplicación para que los cambios tengan efecto en las tareas automáticas."
        
     return message