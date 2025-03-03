from time import strftime
from asyncio import new_event_loop, sleep
from email.mime.text import MIMEText
from os import environ
from jinja2 import Environment, FileSystemLoader, Template
from concurrent.futures import ThreadPoolExecutor

from logger import app_logger
from database import Database
from utils import Mailer, check_mailer

def send_mail_to_users(uslice: list[any], fee: int, template: Template, payment_url: str):
    mailer = Mailer()

    for user in uslice:
        message = MIMEText(template.render(count=fee, url=payment_url), "html")

        message.add_header("Subject", f"Asistencia de pagos - Pago de la cuota {fee}")
        message.add_header("From", environ["SMTP_FROM_ADDRESS"])
        message.add_header("To", user[0])

        mailer.send_mail(message)
    
    mailer.end()

async def notification_task(dates: list[str], notification_count: int, payment_url: str):
    EMAIL_ENV = Environment(loader=FileSystemLoader("templates"))

    while True:
        await sleep(1)
        curr_date = strftime("%Y-%m-%d")
    
        # It's the payment date
        if dates[notification_count - 1] == curr_date:
            db = Database()
            
            number = notification_count
            users = db.execute_query("SELECT email FROM users WHERE send_notifications=TRUE")
            users_size = len(users)

            c = 32 if users_size > 32 else 1
            slices_size = users_size // c
            k = users_size % c

            step = lambda x : slices_size*x
            template = EMAIL_ENV.get_template("email/payment_near.html")
            pool = ThreadPoolExecutor(max_workers=20)

            for i in range(0, c):
                pool.submit(send_mail_to_users, uslice=users[step(i):step(i + 1)], 
                            fee=number, template=template, payment_url=payment_url)
                
            if k != 0:
                pool.submit(send_mail_to_users, uslice=users[slices_size*c:slices_size*c + k],
                                   fee=number, template=template, payment_url=payment_url)
            
            pool.shutdown(wait=True)

            # Now, move the cursor to wait for the next payment date.
            notification_count += 1
            if notification_count > 5: notification_count = 1

            db.execute_update(f"UPDATE data SET value={notification_count} WHERE key='notification_next_payment_day'")
            
def create_notification_task(payment_url: str, dates: list[str]):
    if not check_mailer():
        app_logger.warning("Mailer does not seems to work properly.")
        app_logger.warning("Task for email notifications will not be started, please fix the problem and restart the app")
        return

    loop = new_event_loop()
    db = Database()
    count = db.execute_query("SELECT value FROM data WHERE key='notification_next_payment_day'")[0][0]

    loop.create_task(notification_task(dates, count, payment_url), name="emails-task")
    app_logger.info("Notifications task initialized succesfully.")

    # Just keep running it. Forever.
    loop.run_forever()