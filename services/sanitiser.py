"""
services/sanitiser.py
"""

import re
import logging
import bleach

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 4000

_INJECTION_PATTERNS = [
    r"ignore all",
    r"ignore (all |previous |above |prior )?(instructions?|prompts?|context)",
    r"disregard (all |previous |above |prior )?(instructions?|prompts?|context)",
    r"forget (everything|all|what i said)",
    r"you are now",
    r"act as (a |an )?",
    r"pretend (to be|you are)",
    r"jailbreak",
    r"bypass (safety|restrictions?|filters?)",
    r"new (system |)prompt",
    r"override (safety|restrictions?)",

]

_INJECTION_RE = re.compile(
    "|".join(_INJECTION_PATTERNS),
    flags=re.IGNORECASE,
)

class InputValidationError(ValueError):
    pass

def sanitise_input(text, field_name="input"):
    if not isinstance(text, str):
        raise InputValidationError(f"{field_name} must be a string")

    text = text.strip()

    if not text:
        raise InputValidationError(f"{field_name} must not be empty")

    if len(text) > MAX_INPUT_LENGTH:
        raise InputValidationError(
            f"{field_name} exceeds maximum length of {MAX_INPUT_LENGTH} characters"
        )

    clean = bleach.clean(text, tags=[], attributes={}, strip=True)

    match = _INJECTION_RE.search(clean)
    if match:
        logger.warning("Injection attempt in '%s': %s", field_name, match.group(0))
        raise InputValidationError(f"{field_name} contains disallowed content")

    clean = re.sub(r"\s{3,}", "  ", clean).strip()
    return clean