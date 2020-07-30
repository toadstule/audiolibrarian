import string


def get_filename(title):
    allowed_chars = string.ascii_letters + string.digits + "_"
    no_underscore_replace = ".,!'\""
    result = []
    for ch in title:
        if ch in allowed_chars:
            result.append(ch)
        elif ch not in no_underscore_replace:
            result.append("_")
    return "".join(result).rstrip("_")
