from flask.blueprints import Blueprint
from flask import request, session, redirect, render_template, url_for, flash, get_flashed_messages
from flask import current_app as app
from hashlib import sha256
from database import Database
from utils import match_regex
from utils import generate_token, Mailer
from email.mime.text import MIMEText

account = Blueprint("account", __name__)

@account.route("/login", methods=["POST", "GET"])
def login():
    # Don't allow authenticated users to see this page.
    if "user" in session:
        return redirect("/", 303)

    if request.method == "POST":
        # Check the user credentials
        email = request.form.get("email", "")
        passwd = request.form.get("password", "")

        if passwd == "" or email == "":
            flash("Rellena todos los campos", "error")
            return redirect("/account/login")
        
        passwd_hash = sha256(passwd.encode()).digest().hex()
        db = Database()

        result = db.execute_query("SELECT id,fname,lname,role,email FROM users WHERE email = ? and password = ?", email, passwd_hash)
        db.close()

        if len(result) < 1:
            flash("Credenciales inválidas", "error")
            return redirect("/account/login")
        
        session["id"] = result[0]
        session["fname"] = result[1]
        session["lname"] = result[2]
        session["role"] = result[3]
        session["email"] = result[4]
        
        if session["role"] == "admin":
            return redirect("/admin/", 302)
        
        return redirect("/", 302)
    
    return render_template("account/login.html", messages=get_flashed_messages(True))

@account.route("/register", methods=["POST", "GET"])
def register():
    # Don't allow authenticated users to see this page.
    if "role" in session:
        return redirect("/", 303)

    if request.method == "POST":
        email = request.form.get("email", "")
        passwd = request.form.get("password", "")
        fname = request.form.get("fname", "")
        lname = request.form.get("lname", "")

        message = None

        # Check if some value is empty
        for value in request.form.values():
            if value == "":
                message = "Rellena todos los campos."
                break
        
        if not match_regex(email, r"^\w+@\w+(?:\.\w+)+$"):
             message = "Introduce un correo válido."
        
        if not match_regex(fname + lname, r"^[a-zA-Z]+$"):
             message = "Introduce un primer y segundo nombre válidos."

        if len(passwd) < 6:
             message = "La contraseña debe tener por lo menos 6 carácteres."

        if message != None:
            flash(message, "error")
            return redirect("/account/register")
             
        passwd_hash = sha256(passwd.encode()).digest().hex()

        db = Database()
        result = db.execute_query("SELECT id FROM users WHERE email = ?", email)

        if len(result) > 0:
            flash(f"Ya existe un usuario registrado con el correo {email}.", "error")
            return redirect("/account/register")

        db.execute_update("INSERT INTO users VALUES (NULL, ?, ?, ?, ?, 'user', TRUE, NULL, json_array())", email, fname, lname, passwd_hash)
        db.close()
        
        flash("Registro completado exitosamente. Ahora inicia sesión", "success")
        return redirect("login", 303)
    
    return render_template("account/register.html", messages=get_flashed_messages(True))

@account.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form.get("email", "")
        db = Database()

        if not match_regex(email, r"^\w+@\w+(?:\.\w+)+$"):
            return render_template("account/forgot.html", message="Introduce un correo válido.")
        
        result = db.execute_query("SELECT id FROM users WHERE email = ?", email)

        if len(result) > 0:
            token = generate_token()
            mailer = Mailer()
    
            text = render_template("email/reset_password.html", req=request, url=url_for("account.reset_password", _external=True, token=token))
            email_template = MIMEText(text, "html")
            
            email_template.add_header("Subject", "Asistencia de pagos - Reinicio de contraseña")
            email_template.add_header("From", app.config["FROM_EMAIL"])
            email_template.add_header("To", email)
            
            if not mailer.send_mail(email_template): 
                return render_template("account/forgot.html",
                                        message="Un error extraño ha ocurrido al enviar el correo. Por favor notifica a los administradores."), 500
            
            # TODO: Set an expiry time for the token, as this can leverage vulnerabilities.
            db.execute_update("UPDATE users SET password_token = ? WHERE id = ?", token, result[0])
        
        db.close()
        return render_template("account/forgot.html", 
                               message="Hemos enviado un correo de recuperación a la cuenta, en caso de existir.")
    
    return render_template("account/forgot.html")

@account.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    query_string = request.query_string.decode("utf-8", errors="ignore").split("=")
    db = Database()
    token = ""
    user = None

    try:
        token = query_string[query_string.index("token") + 1]
        result = db.execute_query("SELECT id FROM users WHERE password_token = ?", token)

        if len(result) == 0:
            raise ValueError
        
        user = result[0]

        if request.method == "POST":
            passwd = request.form.get("new_password", "")
            if len(passwd) < 6:
                return render_template("account/reset_password.html", 
                                       message="Por favor, introduce una contraseña con mínimo 6 carácteres.")

            passwd_hash = sha256(passwd.encode()).digest().hex()

            db.execute_update("UPDATE users SET password = ?, password_token = NULL WHERE id = ?", passwd_hash, user)

            return redirect("/account/login", 301)
        
        return render_template("account/reset_password.html")
    except ValueError:
        return redirect("/", 303)
    finally:
        db.close()

@account.route("/profile", methods=["GET", "POST"])
def profile():
    if "role" not in session:
        return redirect("/", 303)
    
    db = Database()
    message = None
    sid = session.get("id")

    if request.method == "POST":
        fname = request.form.get("fname", "")
        lname = request.form.get("lname", "")
        notifications = False if request.form.get("enable_notifications") == None else True
        
        if fname == "" or lname == "":
            message = "Por favor, rellena los campos"
        
        if not match_regex(fname + lname, r"^[a-zA-Z]+$"):
            message = "Utiliza solo letras en tu nombre."

        if not message:
            db.execute_update("UPDATE users SET fname = ?,lname = ?,send_notifications = ? WHERE id = ?",
                          fname, lname, notifications, sid)
            session["fname"] = fname
            session["lname"] = lname
            
            message = "Datos actualizados correctamente."

    user_data = db.execute_query("SELECT fname,lname,email,send_notifications FROM users WHERE id = ?", sid)
    db.close()

    return render_template("account/profile.html", data=user_data, message=message) 

@account.get("/logout")
def logout():
    session.clear()

    return redirect("/", 301)