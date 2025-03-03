# This task will add the fee number as pending to users when the payment date is meet.
from asyncio import new_event_loop, sleep
from json import dumps, loads
from time import strftime, localtime

from database import Database
from logger import app_logger

def update_users_slice(users_slice: list[any], fee: int, cursor):
    for user in users_slice:
        json: list[int] = loads(user[1])
        json.append(fee)
        cursor.execute("UPDATE users SET pending_fees=json(?) WHERE id=?",  [dumps(json), user[0]])


async def fee_task(dates: list[str]):
    db = Database()
    result = db.execute_query("SELECT value FROM data WHERE key='payment_date'")
    
    if not len(result) > 0:
        today_fee = None
    else:
        today_fee = result[0][0]

    while True:
        await sleep(1)

        date = strftime("%Y-%m-%d", localtime())

        if not today_fee:
            for i, fee_date in enumerate(dates):
              if fee_date == date:
                  users = db.execute_query("SELECT id,pending_fees FROM users WHERE NOT role='admin'")
                  users_size = len(users)

                  c = 32 if users_size > 32 else 1
                  slices_size = users_size // c
                  k = users_size % c

                  step = lambda x : slices_size*x
                  sup = slices_size*c
                  cursor = db.get_raw_cursor()

                  for j in range(0, c):
                      update_users_slice(users[step(j):step(j + 1)], i + 1, cursor)
                      
                  if k != 0:
                      update_users_slice(users[sup:sup + k], i + 1, cursor)

                  cursor.close()
                  db.commit_changes()
                      
                  today_fee = fee_date

                  db.execute_update("INSERT INTO data VALUES ('payment_date', ?)", today_fee)
                  break
        
        if today_fee != date:
            db.execute_update("DELETE FROM data WHERE key='payment_date'")
            today_fee = None
                    
            
def create_fee_updater_task(dates: list[str]):
    loop = new_event_loop()

    loop.create_task(fee_task(dates), name="fees-task")
    app_logger.info("Fees updater task initialized succesfully.")

    # Just keep running it. Forever.
    loop.run_forever()