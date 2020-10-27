import re
import string


uuid_regex = re.compile(r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}", re.I)


def get_filename(title: str) -> str:
    """Convert a title into a filename."""
    allowed_chars = string.ascii_letters + string.digits + "_."
    no_underscore_replace = ",!'\""
    result = []
    for ch in title:
        if ch in allowed_chars:
            result.append(ch)
        elif ch == "&":
            result.extend("and")
        elif ch not in no_underscore_replace:
            result.append("_")
    return "".join(result).rstrip("_")


def get_uuid(text: str) -> (str, None):
    """Return the first UUID found within a given string."""
    match = uuid_regex.search(text)
    if match is not None:
        return match.group()
