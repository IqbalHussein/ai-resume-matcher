import re
from typing import Dict, List
from src.config.skills import ALIASES, STRICT_SKILLS

def _build_reverse_aliases() -> Dict[str, List[str]]:
    """
    Build a reverse alias mapping from canonical skill names to their aliases.
    
    For example, if ALIASES = {"pytorch": "PyTorch", "torch": "PyTorch"},
    this returns {"PyTorch": ["pytorch", "torch"]}.
    
    This allows evidence collection to search for all variations of a skill name.
    
    Returns:
        Dictionary mapping canonical skill names to lists of their alias phrases
    """
    rev: Dict[str, List[str]] = {}
    for alias, canonical in ALIASES.items():
        rev.setdefault(canonical, []).append(alias)
    return rev

REVERSE_ALIASES = _build_reverse_aliases()

def _normalize_line(line: str) -> str:
    """
    Normalize a single line for evidence collection.
    
    Removes HTML entities and collapses whitespace while preserving the line content
    for display purposes.
    
    Args:
        line: Raw text line
        
    Returns:
        Normalized line with cleaned whitespace
    """
    line = line.strip().replace("&nbsp;", " ")
    line = re.sub(r"\s+", " ", line)
    return line

def find_skill_evidence(text: str, skills: List[str], max_lines_per_skill: int = 3) -> Dict[str, List[str]]:
    """
    Find and collect evidence lines showing where skills appear in text.
    
    For each skill in the provided list, searches through the text to find lines
    containing that skill (or its aliases). Returns up to max_lines_per_skill
    evidence lines for each skill found, with line numbers for easy reference.
    
    Uses regex patterns with alphanumeric boundaries to avoid false positives 
    (e.g., prevents matching 'c' inside 'account').
    
    Args:
        text: The text to search (job posting or resume)
        skills: List of skill names to find evidence for
        max_lines_per_skill: Maximum number of evidence lines to collect per skill (default: 3)
        
    Returns:
        Dictionary mapping skill names to lists of evidence strings.
        Each evidence string is formatted as "L{line_number}: {line_content}".
        Only skills with evidence found are included in the result.
    """
    lines = [_normalize_line(l) for l in text.splitlines()]
    lines = [l for l in lines if l]  # drop empties

    out: Dict[str, List[str]] = {}

    for skill in skills:
        evidence: List[str] = []
        
        # Build search patterns: canonical name + aliases
        needles = [skill]
        for alias in REVERSE_ALIASES.get(skill, []):
            needles.append(alias)
            
        # Combine into a single regex with alphanumeric boundaries
        # This handles short skills (C) and special chars (C++, C#) safely
        patterns = [rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])" for n in needles]
        combined_pat = re.compile("|".join(patterns), re.IGNORECASE)

        for i, line in enumerate(lines, start=1):
            if combined_pat.search(line):
                evidence.append(f"L{i}: {line}")
                if len(evidence) >= max_lines_per_skill:
                    break
        
        if evidence:
            out[skill] = evidence

    return out
