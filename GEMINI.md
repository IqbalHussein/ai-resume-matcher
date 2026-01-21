# GEMINI.md — AI Resume Matcher

## Project Overview
AI Resume Matcher is a modular Python project that ingests:
- raw job postings (text),
- a candidate resume (text or PDF),

and produces:
- structured skill extraction,
- weighted job–resume matching,
- explainable match results with skill evidence,
- machine-readable reports (JSON) suitable for UI or further analysis.

This project prioritizes:
- interpretability over black-box scoring,
- modular design,
- clean separation of parsing, matching, and orchestration logic.

---

## Documentation

- Streamlit (UI framework)  
  https://docs.streamlit.io/

- Sentence Transformers / Embeddings  
  https://www.sbert.net/

- OpenAI Embeddings API  
  https://platform.openai.com/docs/guides/embeddings

- spaCy (advanced NLP)  
  https://spacy.io/usage

- pypdf (PDF parsing)
  https://pypdf.readthedocs.io/en/latest/

### Documentation Updates

**Update this GEMINI.md file** when the user confirms changes are good:
- New commands or scripts
- Architechture changes
- New conventions or patterns

## High-Level Architecture

```
ai-resume-matcher/
├── data/
│   ├── sample-postings.txt
│   ├── structured_jobs.json
│   ├── resume.txt
│   ├── resume.pdf (optional)
│   ├── resume_structured.json
│   └── match_report.json
│
├── src/
│   ├── config/
│   │   ├── skills.py
│   │   └── weights.py
│   │
│   ├── parsing/
│   │   ├── text_utilities.py
│   │   ├── skills_extraction.py
│   │   ├── job_parser.py
│   │   └── resume_parser.py
│   │
│   ├── matching/
│   │   ├── matcher.py
│   │   ├── semantic.py
│   │   └── evidence.py
│   │
│   └── __init__.py
│
├── main.py
├── streamlit_app.py
├── requirements.txt
├── README.md
└── GEMINI.md
```

---

## Entry Point Rules (IMPORTANT)

- `main.py`: CLI entry point. Orchestrates the workflow using files in `data/`.
- `streamlit_app.py`: Web UI entry point. Orchestrates the workflow using user-uploaded files.
- Files inside `src/` are modules, not scripts
- Do NOT add CLI logic or prints inside `src/` modules
- All orchestration belongs in entry points (`main.py` or `streamlit_app.py`)

Run the project using:
```bash
python main.py
# OR
streamlit run streamlit_app.py
```

## UI Design Principles (Streamlit)
- **Visual Hierarchy:** Use columns, expanders, and headers to organize information.
- **Feedback:** Use spinners for long-running operations and success/error messages for status.
- **Clarity:** Clearly label inputs and outputs. Use metrics for high-level scores.

---

## Core Data Contracts (DO NOT BREAK)

### Job Record
```python
{
  "id": int,
  "title": str,
  "company": str,
  "skills": list[str],
  "text": str
}
```

### Resume Record
```python
{
  "text": str,
  "sections": dict[str, str],
  "skills_all": list[str],
  "skills_section": list[str]
}
```

### Match Result
```python
{
  "title": str,
  "company": str,
  "score": float,
  "semantic_score": float,
  "matched_skills": list[str],
  "missing_skills": list[str],
  "matched_weight": float,
  "total_weight": float,
  "evidence": {
    "job": dict[str, list[str]],
    "resume": dict[str, list[str]]
  }
}
```
---

## Style Rules
- Never include in-line comments. Include docstrings for functions.
- Never use emojis.
- Follow existing conventions within the codebase.
---

## Testing Expectations

Manual testing via main.py is acceptable

Outputs should be visually inspectable via JSON files

Deterministic behavior is preferred over probabilistic outputs

## Summary for Gemini
This is a modular, rule-based, explainable AI system.
Optimize for clarity, correctness, and maintainability.

When modifying or extending this project:

### DO

Respect module boundaries

Reuse existing utilities instead of duplicating logic

Keep outputs JSON-serializable

Maintain backward compatibility of data contracts

Ask before introducing new dependencies

### DO NOT

Collapse modules back into a single script

Add side effects to parsing functions

Print from inside src/ modules

Introduce hidden heuristics or opaque scoring

Change file paths without updating main.py