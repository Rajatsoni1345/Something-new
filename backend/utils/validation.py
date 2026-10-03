import re

def is_valid_uuid(s):
    if not s or not isinstance(s, str):
        return False
    return bool(re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s.lower()))

def is_safe_answer(s):
    if not isinstance(s, str):
        return False
    if len(s) > 100:
        return False
    return bool(re.match(r"^[a-zA-Z0-9\s\-_'\.]+$", s))
