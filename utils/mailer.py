# This component is for sending emails about notifications and payments stuff.
# As you see, the app will only connect to SMTP servers with SSL enabled; this is for
# security reasons.
import smtplib

from email.message import EmailMessage
from ssl import create_default_context
from os import environ
from socket import gaierror

from logger import app_logger

class Mailer:
    def __init__(self):
        self.server = None
        
        try:
            if environ["SMTP_SSL"] == "true":
                ctx = create_default_context()
                self.server = smtplib.SMTP_SSL(environ["SMTP_HOST"], int(environ["SMTP_PORT"]), context=ctx,
                                               timeout=5)
            else:
                self.server = smtplib.SMTP(environ["SMTP_HOST"], int(environ["SMTP_PORT"]), timeout=5)

            self.server.user = environ["SMTP_USER"]
            self.server.password = environ["SMTP_PASSWORD"]
            self.server.auth_login()
            self.server.ehlo_or_helo_if_needed()
        except smtplib.SMTPAuthenticationError:
            app_logger.error("The user/password pair for the SMTP server is invalid! check your credentials in the environment file")
            self.server = None
        except (ConnectionRefusedError, gaierror, TimeoutError, smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError):
            app_logger.error("Could not connect to the SMTP server! check if the server is up and working")
        except OSError as e:
            app_logger.error(f"OS Exception ocurred while connecting to SMTP server: {e}")
        except smtplib.SMTPHeloError:
            app_logger.warning("Server didn't properly answer to the HELO command! Mailer may not work properly")

    # Sends an email with the configured SMTP server.
    # returns a status code, 1 means that the email was sent successfully.
    def send_mail(self, message: EmailMessage) -> int:
        if self.server == None: return 0

        try:
            self.server.send_message(message)
            return 1
        except smtplib.SMTPException:
            app_logger.error(f"An error happened while sending email to {message.get("To")}!")
            raise

    def end(self):
        if self.server == None: return

        self.server.close()