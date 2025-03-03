from .checks import *
from .mailer import *
from .config import *

import string
import random

# Generic utilities

def generate_token(length: int = 32):
    alphabet = string.ascii_letters + string.digits
    token = []

    for _ in range(0, length):
        rand = random.randrange(0, len(alphabet))
        token.append(alphabet[rand])

    return "".join(token)