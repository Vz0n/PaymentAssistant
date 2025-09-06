from flask.blueprints import Blueprint
from flask import request, session, render_template, redirect, url_for, flash, get_flashed_messages
from flask import current_app as app
from hashlib import sha256
from database import Database
from utils import match_regex, generate_token, Mailer

account = Blueprint("account", __name__)

@account.before_request
def check_user():
    # Routes that only guests can access to
    guest_rules = ["account.login", "account.register", "account.forgot", 
                   "account.reset_password"]

    if request.url_rule.endpoint in guest_rules:
        if "id" in session:
          return redirect("/", 302)
    else:
        if "id" not in session:
          return redirect("/account/login", 302)

@account.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        passwd = request.form.get("password", "")
        
        if not match_regex(email, r"^\w+@\w+(?:\.\w+)+$"):
            flash("Introduce un correo válido.", "error")
            return redirect("login", 303)
        
        passwd_hash = sha256(passwd.encode()).digest().hex()
        db = Database()

        result = db.execute_query("SELECT id,role FROM users WHERE email = ? AND password = ?", email, passwd_hash)
        db.close()

        if len(result) < 1:
            flash("Credenciales inválidas", "error")
            return redirect("login", 303)
        
        session["id"] = result[0][0]
        session["role"] = result[0][1]
        
        return redirect("/", 302)
    
    return render_template("account/login.html", messages=get_flashed_messages(True))

@account.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "")
        passwd = request.form.get("password", "")
        fname = request.form.get("fname", "")
        sname = request.form.get("sname", "")
        message = None
        
        if not match_regex(email, r"^\w+@\w+(?:\.\w+)+$"):
             message = ("Introduce un correo válido.", "error")
        
        if not match_regex(fname, r"^[a-zA-Z]+$") or not match_regex(sname, r"^[a-zA-Z]+$"):
             message = ("Introduce nombres válidos.", "error")

        if len(passwd) < 6:
             message = ("La contraseña debe tener por lo menos 6 carácteres.", "error")

        if message:
            flash(*message)
            return redirect("register", 303)
             
        passwd_hash = sha256(passwd.encode()).digest().hex()

        db = Database()
        result = db.execute_query("SELECT id FROM users WHERE email = ?", email)

        if len(result) > 0:
            flash("Ya existe un usuario registrado con ese correo.", "error")
            return redirect("register", 303)

        db.execute_update("INSERT INTO users VALUES (NULL, ?, ?, ?, ?, 'user', TRUE, NULL, json_array())", email, fname, sname, passwd_hash)
        db.close()
        
        flash("Registro completado exitosamente. Ahora inicia sesión", "success")
        return redirect("login", 302)
    
    return render_template("account/register.html", messages=get_flashed_messages(True))

@account.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "")
        db = Database()

        if not match_regex(email, r"^\w+@\w+(?:\.\w+)+$"):
            flash("Introduce un correo válido.", "error")
            return redirect("forgot", 303)
        
        result = db.execute_query("SELECT id FROM users WHERE email = ?", email)

        if len(result) > 0:
            token = generate_token()
            mailer = Mailer()
    
            text = render_template("email/reset_password.html", req=request, 
                                   url=url_for("account.reset_password", _external=True, token=token))
            
            if not mailer.send_html_mail(text, app.config["FROM_EMAIL"], email, 
                                         "Reinicio de contraseña"): 
                flash("Un error extraño ha ocurrido al enviar el correo. Por favor notifica a los administradores.", "error")
                return redirect("forgot", 303)
            
            # TODO: Set an expiry time for the token, as this can leverage vulnerabilities.
            db.execute_update("UPDATE users SET password_token = ? WHERE id = ?", token, result[0][0])
        
        db.close()
        flash("Hemos enviado un correo de recuperación a la cuenta, en caso de existir.", "success")
    
    return render_template("account/forgot.html", messages=get_flashed_messages(True))

@account.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    db = Database()
    user = None

    try:
        if not match_regex(token, r"^[a-zA-Z0-9]{32}$"):
            raise ValueError

        result = db.execute_query("SELECT id FROM users WHERE password_token = ?", token)

        if len(result) == 0:
            raise ValueError
        
        user = result[0][0]

        if request.method == "POST":
            passwd = request.form.get("new_password", "")
            passwd_confirm = request.form.get("new_password_confirm", "")
            message = None

            if len(passwd) < 6:
                message = ("Por favor, introduce una contraseña con mínimo 6 carácteres.", "error")

            if passwd != passwd_confirm:
                message = ("Las contraseñas no coinciden.", "error")
            
            if not message:
                passwd_hash = sha256(passwd.encode()).digest().hex()
                db.execute_update("UPDATE users SET password = ?, password_token = NULL WHERE id = ?", passwd_hash, user)

                flash("Contraseña reiniciada exitósamente.", "success")
                return redirect("/account/login", 301)
            else:
                flash(*message)
        
        return render_template("account/reset_password.html", messages=get_flashed_messages(True))
    except ValueError:
        return redirect("/", 303)
    finally:
        db.close()

@account.route("/change_password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        # There is no need to check the size of the old password, as it is impossible
        # to set one with < 6 characters.
        old_passwd = sha256(request.form.get("old_password", "").encode()).digest().hex()
        new_passwd = request.form.get("new_password", "")
        confirm = request.form.get("new_password_confirm", "")
        message = None

        db = Database()
        user_id = session["id"]
        user_passwd = db.execute_query("SELECT password FROM users WHERE id = ?", user_id)[0][0]

        if len(new_passwd) < 6:
            message = ("Por favor, introduce una contraseña con mínimo 6 carácteres.", "error")

        if new_passwd != confirm:
            message = ("Las contraseñas no coinciden.", "error")

        if user_passwd != old_passwd:
            message = ("Has introducido una contraseña incorrecta.", "error")
            
        if not message:
            passwd_hash = sha256(new_passwd.encode()).digest().hex()
            db.execute_update("UPDATE users SET password = ? WHERE id = ?", passwd_hash, user_id)
            
            message = ("Contraseña actualizada exitósamente.", "success")
            
        flash(*message)
        
    return render_template("account/change_password.html", messages=get_flashed_messages(True))

@account.route("/profile", methods=["GET", "POST"])
def profile():    
    db = Database()
    sid = session.get("id")
    message = None

    if request.method == "POST":
        fname = request.form.get("fname", "")
        sname = request.form.get("sname", "")
        notifications = False if request.form.get("enable_notifications") == None else True
        
        if not match_regex(fname, r"^[a-zA-Z]+$") or not match_regex(sname, r"^[a-zA-Z]+$"):
            message = ("Por favor, utiliza solo letras en tu nombre.", "error")

        if not message:
            db.execute_update("UPDATE users SET fname = ?, sname = ?, send_notifications = ? WHERE id = ?",
                          fname, sname, notifications, sid)
            
            message = ("Datos actualizados correctamente.", "success")

        flash(*message)

    user_data = db.execute_query("SELECT fname,sname,email,send_notifications FROM users WHERE id = ?", sid)[0]
    db.close()

    return render_template("account/profile.html", data=user_data, messages=get_flashed_messages(True)) 

@account.get("/logout")
def logout():
    session.clear()

    return redirect("/", 301)