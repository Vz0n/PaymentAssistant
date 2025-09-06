import re

from .mailer import Mailer

def match_regex(string: str, regexp: str):
    reg = re.compile(regexp)

    return reg.match(string)

def get_valid_dates(dates: list[str]):
    count = 0

    for date in dates:
        if match_regex(date, r"([0-9]{4}-[0-9]{2}-[0-9]{2})"):
            count += 1

    return count

def check_mailer() -> int:
    mailer = Mailer()
    mailer.end()

    return (mailer.server != None)