import spacy
from spacy.language import Language
from src.config.skills import ALIASES, STRICT_SKILLS, SOFT_ENG_SKILLS

_nlp = None

def _get_nlp() -> Language:
    """
    Load and configure the spaCy model with a custom EntityRuler for skills.
    
    The model is cached in a global variable to avoid reloading overhead.
    Patterns are generated from STRICT_SKILLS, ALIASES, and SOFT_ENG_SKILLS.
    """
    global _nlp
    if _nlp is not None:
        return _nlp
    
    nlp = spacy.load("en_core_web_sm")
    
    patterns = []
    
    for key, canonical in STRICT_SKILLS.items():
        if key == "go":
            patterns.append({"label": "SKILL", "pattern": [{"ORTH": "Go"}], "id": canonical})
            patterns.append({"label": "SKILL", "pattern": [{"LOWER": "go", "POS": "PROPN"}], "id": canonical})
            patterns.append({"label": "SKILL", "pattern": [{"LOWER": "golang"}], "id": canonical})
        else:
            doc = nlp.make_doc(key)
            pattern = [{"LOWER": token.text.lower()} for token in doc]
            patterns.append({"label": "SKILL", "pattern": pattern, "id": canonical})

    for alias, canonical in ALIASES.items():
        doc = nlp.make_doc(alias)
        pattern = [{"LOWER": token.text.lower()} for token in doc]
        patterns.append({"label": "SKILL", "pattern": pattern, "id": canonical})

    strict_canonicals = set(STRICT_SKILLS.values())
    
    for skill in SOFT_ENG_SKILLS:
        if skill in strict_canonicals:
            continue
            
        doc = nlp(skill)
        
        pattern_lemma = [{"LEMMA": token.lemma_} for token in doc]
        patterns.append({"label": "SKILL", "pattern": pattern_lemma, "id": skill})
        
        pattern_lower = [{"LOWER": token.text.lower()} for token in doc]
        patterns.append({"label": "SKILL", "pattern": pattern_lower, "id": skill})

    # Add ruler after generating patterns to avoid empty ruler warnings
    ruler = nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(patterns)
    
    _nlp = nlp
    return _nlp

def extract_skills(text: str, soft_eng_skills: list[str]) -> list[str]:
    """
    Extract technical skills from text using a spaCy EntityRuler pipeline.
    
    This approach uses token-level matching and lemmatization to find skills,
    which is more robust than simple substring matching.
    
    Args:
        text: The text to search (job posting or resume)
        soft_eng_skills: List of canonical skill names to filter results against.
        
    Returns:
        Sorted list of unique, canonicalized skill names found in the text.
    """
    if not text.strip():
        return []

    nlp = _get_nlp()
    
    doc = nlp(text)
    
    found = set()
    allowed_skills = set(soft_eng_skills)
    
    for ent in doc.ents:
        if ent.label_ == "SKILL":
            canonical = ent.ent_id_
            if canonical in allowed_skills:
                found.add(canonical)
            
    return sorted(list(found))
