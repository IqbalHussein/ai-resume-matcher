import json
import os
from datetime import datetime
from src.parsing.job_parser import parse_jobs_from_file
from src.parsing.resume_parser import parse_resume_from_file
from src.matching.matcher import match_resume_to_jobs

def main():
    """
    Main entry point for the AI Resume Matcher application.
    
    This function orchestrates the complete workflow:
    1. Parses job postings from a text file and saves structured data to JSON
    2. Parses resume from a text or PDF file and saves structured data to JSON
    3. Matches resume skills against job requirements
    4. Displays top 5 job matches with scores and skill breakdowns
    5. Generates a comprehensive match report saved to JSON
    
    The matching algorithm uses weighted skill scoring to rank jobs based on
    how well the resume's skills align with each job's requirements.
    """
    jobs = parse_jobs_from_file("data/sample-postings.txt")
    with open("data/structured_jobs.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)

    resume_path = "data/resume.txt"
    if os.path.exists("data/resume.pdf"):
        resume_path = "data/resume.pdf"
        print(f"Detected PDF resume: {resume_path}")

    resume = parse_resume_from_file(resume_path)
    with open("data/resume_structured.json", "w", encoding="utf-8") as f:
        json.dump(resume, f, indent=2, ensure_ascii=False)

    # choose which resume skill list to match with
    resume_skills = resume["skills_all"]
    # Pass resume text for semantic matching
    results = match_resume_to_jobs(jobs, resume_skills, resume_content=resume["text"])

    print("\nTop 5 job matches:\n")
    for i, r in enumerate(results[:5], start=1):
        print(f"{i}) {r['title']} — {r['company']} | score={r['score']} | semantic={r.get('semantic_score', 0)} "
            f"({r['matched_weight']}/{r['total_weight']})")
        print("   matched:", ", ".join(r["matched_skills"]) if r["matched_skills"] else "None")
        print("   missing:", ", ".join(r["missing_skills"][:12]) + (" ..." if len(r["missing_skills"]) > 12 else ""))
        print()

    #Build match report
    match_report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "resume":{
            "skills_used": resume_skills
        },
        "results": []
    }

    for rank, r in enumerate(results, start=1):
        match_report["results"].append({
            "rank": rank,
            "title": r["title"],
            "company": r["company"],
            "score": round(r["score"], 3),
            "semantic_score": r.get("semantic_score", 0),
            "matched_skills": r["matched_skills"],
            "missing_skills": r["missing_skills"]
        })
    
    with open("data/match_report.json", "w", encoding="utf-8") as f:
        json.dump(match_report, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
