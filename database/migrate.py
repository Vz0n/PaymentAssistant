from os import urandom
from hashlib import sha256
from sqlite3 import OperationalError

from . import Database
from utils import app_logger

random_passwd = urandom(12).hex().encode()
schema_version = 2

# Sequence of SQL statements
MIGRATION_SQL = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email VARCHAR(32) NOT NULL, fname VARCHAR(32), lname VARCHAR(32), password VARCHAR(64) NOT NULL, role TEXT CHECK(role IN ('user', 'admin')), send_notifications INTEGER, password_token VARCHAR(32), pending_fees TEXT)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_email ON users (email)",
    "CREATE TABLE IF NOT EXISTS data (key TEXT, value INTEGER)",
    "CREATE TABLE IF NOT EXISTS verif_pending_payments (id VARCHAR(16) PRIMARY KEY, user REFERENCES users(id), fee_number INTEGER, transaction_id INTEGER, ci INTEGER)",
    f"INSERT OR REPLACE INTO data VALUES ('schema_version', {schema_version})"
]

SEED_SQL = [
    f"INSERT INTO users VALUES (1, 'admin@example.com', 'Administrator', NULL, '{sha256(random_passwd).digest().hex()}', 'admin', FALSE, NULL, json_array())",
    "INSERT INTO data VALUES ('notification_next_payment_day', 1)"
]

def check_migration():
    db = Database()
    app_logger.info("Checking migrations...")

    try:
       # If the table does not exists, this will throw an error and
       # it will run the migrations.
       # TODO: Change this to something better
       db_version = db.execute_query("SELECT value FROM data WHERE key='schema_version'")[0]

       if db_version < schema_version:
           app_logger.info("Updating database schema...")
           db.run_update_statements(MIGRATION_SQL)

    except OperationalError:
       app_logger.info("Running migrations and seeding...")
       app_logger.info(f"The default user Administrator (admin@example.com) will be generated with password {random_passwd.decode()}")
       app_logger.info("Copy this password as it won't be show again.")
       db.run_update_statements(MIGRATION_SQL)
       db.run_update_statements(SEED_SQL)

    finally:
       app_logger.info("Check successful.")  