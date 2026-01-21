import re
from typing import Dict, List, Optional
from src.parsing.text_utilities import read_text_file, read_pdf_file, normalize_text
from src.config.skills import SOFT_ENG_SKILLS
from src.parsing.skills_extraction import extract_skills


CANONICAL_SECTIONS = [
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "leadership",
    "awards",
    "publications",
    "other",
]

# Heading aliases -> canonical section
HEADING_ALIASES = {
    # Summary
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "objective": "summary",

    # Skills
    "skills": "skills",
    "technical skills": "skills",
    "technologies": "skills",
    "tech stack": "skills",
    "relevant skills, experiences and accomplishments": "skills",

    # Experience
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "employment history": "experience",

    # Projects
    "projects": "projects",
    "personal projects": "projects",
    "selected projects": "projects",
    "project experience": "projects",

    # Education
    "education": "education",
    "academic background": "education",

    # Certifications
    "certifications": "certifications",
    "certificates": "certifications",
    "licenses": "certifications",

    # Leadership
    "leadership": "leadership",
    "leadership experience": "leadership",
    "activities": "leadership",
    "extracurricular": "leadership",

    # Awards
    "awards": "awards",
    "honors": "awards",
    "honours": "awards",

    # Publications
    "publications": "publications",
}

BULLET_PREFIXES = ("-", "•", "*", "–", "—")

def _normalize_heading(line: str) -> str:
    """
    Normalize a candidate heading line for consistent matching.
    
    Performs the following transformations:
    - Converts to lowercase
    - Removes trailing colon
    - Collapses multiple spaces into single spaces
    - Strips punctuation and noise characters from edges
    
    Args:
        line: Raw heading line to normalize
        
    Returns:
        Normalized heading string ready for alias matching
    """
    s = line.strip().lower()
    s = s.rstrip(":")
    s = re.sub(r"\s+", " ", s)
    s = s.strip(" -•*–—\t")
    return s

def _looks_like_heading(line: str) -> bool:
    """
    Determine if a line appears to be a section heading.
    
    Uses multiple heuristics:
    - Short-ish line (under 60 characters)
    - Not a bullet point line
    - Either matches a known heading alias (case-insensitive) OR is all-caps and heading-like
    
    Args:
        line: Text line to evaluate
        
    Returns:
        True if line appears to be a section heading, False otherwise
    """
    raw = line.strip()
    if not raw:
        return False

    # Bullet lines are content, not headings
    if raw.startswith(BULLET_PREFIXES):
        return False

    # Too long to be a heading
    if len(raw) > 60:
        return False

    norm = _normalize_heading(raw)

    # Direct match to known headings
    if norm in HEADING_ALIASES:
        return True

    if raw.isupper() and 3 <= len(raw) <= 30 and any(c.isalpha() for c in raw):
        if len(raw.split()) >= 2 or norm in {"education", "projects", "experience", "skills"}:
            return True

    return False

def split_resume_sections(resume_text: str) -> Dict[str, str]:
    """
    Split a normalized resume text into sections based on heading lines.
    
    Identifies section headings and groups content under canonical section names
    (summary, skills, experience, projects, education, etc.). Any text before the
    first detected heading becomes "summary" if non-empty. Unknown headings are
    stored under "other".
    
    Args:
        resume_text: Normalized resume text with consistent line endings
        
    Returns:
        Dictionary mapping canonical section names to their text content.
        Only sections with content are included in the result.
    """
    lines = resume_text.split("\n")

    sections: Dict[str, List[str]] = {k: [] for k in CANONICAL_SECTIONS}
    current_section: Optional[str] = None
    preamble: List[str] = []

    def flush_preamble_into_summary():
        nonlocal preamble
        text = "\n".join([ln for ln in preamble if ln.strip()]).strip()
        if text:
            sections["summary"].append(text)
        preamble = []

    for line in lines:
        if _looks_like_heading(line):
            # We hit a new section heading
            heading_norm = _normalize_heading(line)
            canonical = HEADING_ALIASES.get(heading_norm, "other")

            # If this is the first heading, preamble becomes summary
            if current_section is None:
                flush_preamble_into_summary()

            current_section = canonical
            continue

        # Normal content line
        if current_section is None:
            preamble.append(line)
        else:
            sections[current_section].append(line)

    # End: if we never saw a heading, everything becomes summary
    if current_section is None:
        flush_preamble_into_summary()
    else:
        # if there's leftover preamble (rare), treat it as summary
        flush_preamble_into_summary()

    # Join and trim
    out: Dict[str, str] = {}
    for k, lines_list in sections.items():
        text = "\n".join(lines_list).strip()
        if text:
            out[k] = text
    return out

def parse_resume_from_file(filename):
    """
    Parse a resume text or PDF file into structured sections and extract skills.
    
    Reads the resume file (detecting format by extension), normalizes the text,
    splits it into canonical sections (summary, skills, experience, etc.), and
    extracts technical skills both from the entire resume and specifically from
    the skills section.
    
    Args:
        filename: Path to the resume file (.txt or .pdf)
        
    Returns:
        Dictionary containing:
        - 'text': Normalized full resume text
        - 'sections': Dict mapping section names to their content
        - 'skills_all': Skills extracted from entire resume
        - 'skills_section': Skills extracted only from skills section
    """

    if filename.lower().endswith(".pdf"):
        raw_resume = read_pdf_file(filename)
    else:
        raw_resume = read_text_file(filename)

    resume_text = normalize_text(raw_resume)

    
    
    sections = split_resume_sections(resume_text)

    skills_all = extract_skills(resume_text, SOFT_ENG_SKILLS)
    skills_section = extract_skills(sections.get("skills", ""), SOFT_ENG_SKILLS)

    return {
        "text": resume_text,
        "sections": sections,
        "skills_all": skills_all,
        "skills_section": skills_section,
    }