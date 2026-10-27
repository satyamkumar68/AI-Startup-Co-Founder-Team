import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# Common prompt injection patterns targeting LLM instruction override
INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|directives)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
    r"(?i)system\s*:\s*you\s+are",
    r"(?i)new\s+instruction\s*:",
    r"(?i)override\s+(system|developer)\s+prompt",
    r"(?i)bypass\s+all\s+(filters|rules|guardrails)",
    r"(?i)you\s+are\s+now\s+in\s+(developer|unrestricted|god)\s+mode"
]


def sanitize_idea_input(idea_text: str) -> Tuple[str, bool, List[str]]:
    """Sanitize and neutralize prompt injection attempts in user-supplied startup ideas.
    
    Returns:
        (sanitized_text, injection_detected, detected_patterns)
    """
    if not idea_text:
        return "", False, []

    detected: List[str] = []
    sanitized = idea_text.strip()

    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, sanitized)
        if match:
            matched_phrase = match.group(0)
            detected.append(matched_phrase)
            # Neutralize the command by quoting and contextualizing
            sanitized = re.sub(pattern, f"[USER_TEXT_LITERAL: {matched_phrase}]", sanitized)

    is_injection = len(detected) > 0
    if is_injection:
        logger.warning(f"Prompt injection pattern detected in startup idea: {detected}")

    # Enforce strict quotation boundaries
    clean_text = f"<startup_idea>{sanitized}</startup_idea>"
    return clean_text, is_injection, detected
