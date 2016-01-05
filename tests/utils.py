import string

ASCII = bytes(range(0, 127)).decode('ascii')
SLUG = string.ascii_lowercase + string.digits + '_'
DIGITS = string.digits


def nondigit(value):
    return value and not value.isdigit()
