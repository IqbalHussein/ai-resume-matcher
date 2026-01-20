import re
from src.config.skills import ALIASES, STRICT_SKILLS

STRICT_PATTERNS = {
    "go": re.compile(r"(?<![a-z0-9])go(?![a-z0-9])", re.IGNORECASE),
    "sql": re.compile(r"(?<![a-z0-9])sql(?![a-z0-9])", re.IGNORECASE),
    "c++": re.compile(r"(?<![a-z0-9])c\+\+(?![a-z0-9])", re.IGNORECASE),
    "c#": re.compile(r"(?<![a-z0-9])c#(?![a-z0-9])", re.IGNORECASE),
    "c": re.compile(r"(?<![a-z0-9])c(?![a-z0-9])", re.IGNORECASE),
}

def _normalize_for_alias(text: str) -> str:
    """
    Normalize text for consistent alias matching.
    
    Converts text to lowercase, removes HTML entities like &nbsp;, and collapses
    multiple whitespace characters into single spaces for uniform skill matching.
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized lowercase text with collapsed whitespace
    """
    t = text.lower()
    t = t.replace("&nbsp;", " ")
    t = re.sub(r"\s+", " ", t)
    return t

def extract_skills(text: str, soft_eng_skills: list[str]) -> list[str]:
    """
    Extract technical skills from job postings or resumes using a three-phase approach.
    
    Phase A: Uses regex patterns to match strict skills (Go, SQL, C, C++, C#) that
             require word boundary detection to avoid false positives.
    Phase B: Uses substring matching for longer, less ambiguous skills.
    Phase C: Normalizes found skills using the ALIASES dictionary to ensure
             consistent canonical naming (e.g., "pytorch" -> "PyTorch").
    
    Args:
        text: The job posting or resume text to search
        soft_eng_skills: List of canonical skill names to search for
        
    Returns:
        Sorted list of unique, canonicalized skill names found in the text
    """
    found = set()
    text_norm = _normalize_for_alias(text)

    # A) Strict skills (regex)
    for key, canonical in STRICT_SKILLS.items():
        if STRICT_PATTERNS[key].search(text):
            found.add(canonical)

    # B) Longer skills (substring)
    for skill in soft_eng_skills:
        s = skill.strip()
        if not s:
            continue
        if s.lower() in STRICT_SKILLS:
            continue
        if s.lower() in text_norm:
            found.add(s)

    # C) Alias normalization
    normalized = set()
    for s in found:
        key = s.lower().strip()
        normalized.add(ALIASES.get(key, s))

    return sorted(normalized)