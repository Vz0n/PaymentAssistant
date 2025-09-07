# This task just fetches the password_reset_token table in search for expired tokens to
# remove it.
# This task will add the fee number as pending to users when the payment date is meet.
from asyncio import new_event_loop, sleep

from database import Database
from logger import app_logger

async def token_watcher_task():
    db = Database()
    while True:
       await sleep(1)

       expired_tokens = db.execute_query("SELECT token FROM password_reset_tokens WHERE (unixepoch() - creation) > 60*10")

       if len(expired_tokens) > 0:
           for token in expired_tokens:
               db.execute_update("DELETE FROM password_reset_tokens WHERE token = ?", *token)
                                
def create_token_watcher_task():
    loop = new_event_loop()

    loop.create_task(token_watcher_task(), name="fees-task")
    app_logger.info("Reset token watcher task started succesfully.")

    # Just keep running it. Forever.
    loop.run_forever()