from src.config.weights import SKILL_WEIGHTS
from src.matching.evidence import find_skill_evidence
from src.matching.semantic import SemanticMatcher


def match_resume_to_jobs(structured_jobs: list[dict], resume: list[str], resume_content: str = "") -> list[dict]:
    """
    Match a resume against multiple job postings using weighted skill scoring.
    
    For each job, calculates a match score based on the weighted overlap between
    the resume's skills and the job's required skills. Also collects evidence
    (specific text snippets) showing where each matched skill appears in both
    the job posting and resume.
    
    The score is calculated as: (sum of matched skill weights) / (sum of all job skill weights)
    Skills are weighted by importance (e.g., AWS=3.0, Python=2.5, Agile=1.0).
    
    Args:
        structured_jobs: List of job dictionaries with 'skills', 'text', etc.
        resume: List of skill strings from the resume
        resume_content: Full text of the resume for semantic matching
        
    Returns:
        List of match result dictionaries sorted by score (descending), each containing:
        - Basic job info (id, title, company)
        - Match metrics (score, matched_count, matched_weight, total_weight, semantic_score)
        - Skill breakdowns (matched_skills, missing_skills)
        - Evidence snippets showing where skills appear in job and resume
    """
    resume_set = set(resume)
    results = []

    semantic_matcher = None
    if resume_content:
        semantic_matcher = SemanticMatcher()

    for job in structured_jobs:
        job_skills = job.get("skills", [])
        job_set = set(job_skills)

        matched = sorted(job_set & resume_set)

        job_text = job.get("text", "")
        
        semantic_score = 0.0
        if semantic_matcher:
            semantic_score = semantic_matcher.compute_similarity(resume_content, job_text)

        # "resume" is a list of skills. Join them for evidence finding (which expects text)
        resume_skills_text = " ".join(resume)

        job_evidence = find_skill_evidence(job_text, matched)
        resume_evidence = find_skill_evidence(resume_skills_text, matched)

        missing = sorted(job_set - resume_set)

        # Weighted score = matched weight / total job weight
        total_weight = sum(SKILL_WEIGHTS.get(s, 1.0) for s in job_set)
        matched_weight = sum(SKILL_WEIGHTS.get(s, 1.0) for s in matched)
        score = matched_weight / max(1e-9, total_weight)  # avoid divide-by-zero

        results.append({
            "job_id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "score": round(score, 3),
            "semantic_score": round(semantic_score, 3),
            "matched_skills": matched,
            "missing_skills": missing,
            "job_skill_count": len(job_set),
            "matched_count": len(matched),
            "matched_weight": round(matched_weight, 2),
            "total_weight": round(total_weight, 2),
            "evidence": {
                "job": job_evidence,
                "resume": resume_evidence
            }
        })

    results.sort(key=lambda x: (x["score"], x["semantic_score"], x["matched_weight"], x["matched_count"]), reverse=True)
    return results