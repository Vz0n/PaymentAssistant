from .mailer import Mailer

import re

def match_regex(string: str, regexp: str):
    reg = re.compile(regexp, re.MULTILINE)

    return reg.match(string)

def find_matches(string: str, regexp: str):
    reg = re.compile(regexp, re.MULTILINE)

    return reg.findall(string)

def check_mailer() -> int:
    mailer = Mailer()
    mailer.end()

    return (mailer.server != None)