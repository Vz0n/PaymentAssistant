from threading import Thread
from dotenv import load_dotenv
from tasks import create_notification_task, create_fee_updater_task
from database.migrate import check_migration

from os import mkdir
from os.path import exists
from logger import app_logger
from utils import Config, set_app_config
from app import app

config = None

try:
    config = Config()
except Exception as e:
    app_logger.info(f"error loading config file: {e}")
    exit(1)

# Load the environment variables
if not load_dotenv():
    app_logger.error("error: .env file not found. Please rename .env.example to .env and change the values.")
    exit(1)

# Do migrations if there are needed for the database
check_migration()

# Create the storage directory if does not exists
if not exists("storage/"):
    mkdir("storage")

# Start the email notifications thread
app_logger.info("Starting email task...")
emails_thread = Thread(target=create_notification_task, name="emails-thread", 
                        args=[f"{config.get("app_url")}/payment", config.get("fee_dates")], daemon=True)
emails_thread.start()

# Start the fee updater thread
app_logger.info("Starting fees updater task...")
fees_thread = Thread(target=create_fee_updater_task, name="fees-thread", 
                       args=[config.get("fee_dates")], daemon=True)
fees_thread.start()

set_app_config(config, app)

if __name__ == "__main__":
    address, port = config.get("bind").split(":")
    app.run(address, port, debug=config.get("debug"))

