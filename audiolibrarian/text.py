import re
import string

digit_regex = re.compile(r"([0-9]+)")
uuid_regex = re.compile(r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}", re.I)


def alpha_numeric_key(x):
    """A key that can be used for sorting alpha-numeric strings numerically.

    Example:
        from audiolibrarian.text import alpha_numeric_key

        l = ["8__eight", "7__seven", "10__ten", "11__eleven"]
        sorted(l)
        # ['10__ten', '11__eleven', '7__seven', '8__eight']
        sorted(l, key=alpha_numeric_key)
        # ['7__seven', '8__eight', '10__ten', '11__eleven']
    """
    return [int(x) if x.isdigit() else x for x in digit_regex.split(str(x))]


def fix(text: str) -> str:
    """Replace some special characters."""
    replacements = {
        8208: 45,  # hyphen
        8217: 39,  # "smart" single quote
    }
    return "".join([chr(replacements[ord(c)]) if ord(c) in replacements else c for c in text])


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
