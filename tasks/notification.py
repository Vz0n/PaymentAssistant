from time import strftime
from asyncio import new_event_loop, sleep
from os import environ
from jinja2 import Environment, FileSystemLoader, Template
from concurrent.futures import ThreadPoolExecutor

from logger import app_logger
from database import Database
from utils import Mailer, check_mailer

def send_mail_to_users(uslice: list[any], fee: int, template: Template, payment_url: str):
    mailer = Mailer()

    for user in uslice:
        message = template.render(count=fee, url=payment_url)

        mailer.send_html_mail(message, environ["SMTP_FROM_ADDRESS"], user[0], 
                              f"Pago de la cuota {fee}")
    
    mailer.end()

async def notification_task(dates: list[str], payment_url: str):
    EMAIL_ENV = Environment(loader=FileSystemLoader("templates/email"))
    db = Database()

    result = db.execute_query("SELECT value FROM data WHERE key = 'notification_fee_date_index'")
    fee_index = None if len(result) < 1 else result[0][0]

    while True:
        await sleep(1)
        
        curr_date = strftime("%Y-%m-%d")
    
        if not fee_index:
          for i, date in enumerate(dates):
            if date == curr_date: 
              users = db.execute_query("SELECT email FROM users WHERE send_notifications = TRUE AND NOT role = 'admin'")
              users_size = len(users)

              c = 32 if users_size > 32 else 1
              slices_size = users_size // c
              k = users_size % c

              step = lambda x : slices_size*x
              template = EMAIL_ENV.get_template("payment_near.html")
              pool = ThreadPoolExecutor(max_workers=20)

              for i in range(0, c):
                pool.submit(send_mail_to_users, uslice=users[step(i):step(i + 1)], 
                            fee=i + 1, template=template, payment_url=payment_url)
                
              if k != 0:
                pool.submit(send_mail_to_users, uslice=users[slices_size*c:slices_size*c + k],
                                   fee=i + 1, template=template, payment_url=payment_url)
            
              pool.shutdown(wait=True)

              fee_index = i + 1
              db.execute_update(f"INSERT INTO data VALUES ('notification_fee_date_index', {fee_index})")
        
        if fee_index is not None and dates[fee_index - 1] != curr_date:
            db.execute_update(f"DELETE FROM data WHERE key = 'notification_fee_date_index'")
            fee_index = None
            
def create_notification_task(payment_url: str, dates: list[str]):
    if not check_mailer():
        app_logger.warning("Mailer does not seems to work properly.")
        app_logger.warning("Task for email notifications will not be started, please fix the problem and restart the app")
        return

    loop = new_event_loop()    

    loop.create_task(notification_task(dates, payment_url), name="emails-task")
    app_logger.info("Notifications task initialized succesfully.")

    # Just keep running it. Forever.
    loop.run_forever()