#Simple program designed to pull skills from a job posting or resume
import json, re, typing
from collections import Counter
from pathlib import Path

ALIASES = {
    # ML / frameworks
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "huggingface": "HuggingFace",
    "hugging face": "HuggingFace",
    "mlflow": "MLflow",
    "ml flow": "MLflow",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn",

    # Dev practices
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "ci/cd": "CI/CD",
    "test driven development": "Test Driven Development",
    "tdd": "TDD",
}

# Skills that are risky to match by substring
STRICT_SKILLS = {
    "go": "Go",
    "sql": "SQL",
    "c++": "C++",
    "c#": "C#",
}

# Pre-compile regex patterns for strict skills
STRICT_PATTERNS = {
    "go": re.compile(r"(?<![a-z0-9])go(?![a-z0-9])", re.IGNORECASE),
    "sql": re.compile(r"(?<![a-z0-9])sql(?![a-z0-9])", re.IGNORECASE),
    # C++ and C# need symbol-aware boundaries
    "c++": re.compile(r"(?<![a-z0-9])c\+\+(?![a-z0-9])", re.IGNORECASE),
    "c#": re.compile(r"(?<![a-z0-9])c#(?![a-z0-9])", re.IGNORECASE),
}

# Normalize text for alias matching
def _normalize_for_alias(text: str) -> str:
    t = text.lower()
    t = t.replace("&nbsp;", " ")
    t = re.sub(r"\s+", " ", t)
    return t

def extract_skills(job_text: str, soft_eng_skills: list[str]) -> list[str]:
    found = set()
    text_norm = _normalize_for_alias(job_text)

    # --- A) Strict skills (regex) ---
    for key, canonical in STRICT_SKILLS.items():
        if STRICT_PATTERNS[key].search(job_text):
            found.add(canonical)

    # --- B) Longer skills (substring) ---
    for skill in soft_eng_skills:
        s = skill.strip()
        if not s:
            continue

        if s.lower() in STRICT_SKILLS:
            continue

        if s.lower() in text_norm:
            found.add(s)

    # --- C) Alias normalization pass ---
    normalized = set()
    for s in found:
        key = s.lower().strip()
        normalized.add(ALIASES.get(key, s))

    return sorted(normalized)


TITLE_KEYWORDS = (
    "engineer", "developer", "software", "full stack", "full-stack",
    "backend", "front end", "frontend", "platform", "embedded", "mlops"
)

NOISE_SUBSTRINGS = [
    "profile insights",
    "here’s how the job qualifications align with your profile",
    "job details",
    "full job description",
    "benefits",
    "pulled from the full job description",
    "show more",
    "apply",
    "easy apply",
    "promoted by hirer",
    "responses managed off linkedin",
    "matches your job preferences",
    "&nbsp;",
]

META_SUBSTRINGS = [
    "reposted", "clicked apply", "applicants"
]

def clean_lines(job_text: str) -> list[str]:
    lines = [ln.strip() for ln in job_text.splitlines()]
    lines = [ln for ln in lines if ln]  # remove empty
    return lines

def is_noise_line(line: str) -> bool:
    l = line.lower()
    return any(s in l for s in NOISE_SUBSTRINGS)

def is_rating(line: str) -> bool:
    l = line.lower()
    if "out of 5 stars" in l:
        return True
    return bool(re.fullmatch(r"\d(\.\d)?", line.strip()))

def is_job_type(line: str) -> bool:
    l = line.lower()
    return l in {"full-time", "part-time", "contract", "permanent", "internship", "temporary"}

def is_location_or_meta(line: str) -> bool:
    l = line.lower()

    if "·" in line and any(s in l for s in META_SUBSTRINGS):
        return True
    # Canadian provincial & territorial locations
    if any(tok in line for tok in ["ON", "QC", "BC", "AB", "MB", "NS", "NB", "NL", "PE", "SK", "YT", "NT", "NU"]):
        if "·" in line or "," in line or "(" in line:
            return True
    if "hybrid" in l or "remote" in l or "on-site" in l:
        # these are often meta/location lines, not company
        return True
    return False

def title_like(line: str) -> bool:
    l = line.lower()
    if is_noise_line(line):
        return False
    if any(s in l for s in META_SUBSTRINGS):
        return False
    if l.startswith("save "):
        return False
    if " at " in l and l.startswith("save "):
        return False
    if len(line) < 4 or len(line) > 90:
        return False
    return any(k in l for k in TITLE_KEYWORDS)

def extract_title_company(job_text: str) -> tuple[str | None, str | None]:
    lines = clean_lines(job_text)
    if not lines:
        return None, None

    # If it's an "insights overlay" chunk, skip it
    if lines[0].lower() == "profile insights":
        return None, None

    # Remove obvious noise lines (keep order)
    filtered = [ln for ln in lines if not is_noise_line(ln)]

    # ---- TITLE ----
    title = None

    # T1: Indeed-style "- job post"
    for ln in filtered:
        if "- job post" in ln.lower():
            title = ln
            break

    # T2: LinkedIn-style: first title-like line
    if title is None:
        for ln in filtered[:25]:  # usually near top
            if title_like(ln):
                title = ln
                break

    # ---- COMPANY ----
    company = None

    # C1: "Save <title> at <company>"
    for ln in filtered[:60]:
        l = ln.lower()
        if l.startswith("save ") and " at " in l:
            company = ln.split(" at ", 1)[1].strip()
            # strip trailing junk if present
            company = re.split(r"\s{2,}|\s·\s", company)[0].strip()
            break

    # C2: "Company · Location"
    if company is None:
        for ln in filtered[:60]:
            if "·" in ln:
                left = ln.split("·", 1)[0].strip()
                # Avoid meta lines like "Ottawa, ON · Reposted..."
                if left and not is_location_or_meta(ln) and not is_job_type(left):
                    # left side should not itself look like a location
                    if not is_location_or_meta(left) and not is_rating(left):
                        company = left
                        break

    # C3: Indeed-style: next clean line after title
    if company is None and title is not None:
        try:
            t_idx = filtered.index(title)
            for ln in filtered[t_idx + 1 : t_idx + 12]:
                if is_rating(ln) or is_location_or_meta(ln) or is_job_type(ln):
                    continue
                company = ln
                break
        except ValueError:
            pass

    return title, company

with open("sample-postings.txt", "r", encoding="utf-8") as file:
    raw_file_data = file.read()

jobs = raw_file_data.split("====")
soft_eng_skills = [
    #Languages
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "SQL", "Shell", "Bash",

    #ML Frameworks
    "TensorFlow", "Torch", "PyTorch", "Keras", "scikit-learn", "XGBoost", "LightGBM",

    #Data Frameworks
    "NumPy", "Pandas", "Matplotlib", "Seaborn", "Plotly", "SQLAlchemy", "Spark",

    #Natural Language Processing
    "spaCy", "NLTK", "Transformers", "HuggingFace", "BERT", "GPT", "Word2Vec",

    #Work Practices
    "Test Driven Development", "TDD", "CI/CD", "Git", "Version Control", "Unit Testing", "Code Review", "Agile", "Scrum", "Paired Programming",

    #Databases
    "PostgreSQL", "MySQL", "MongoDB", "NoSQL", "Redis", "SQLite",

    #Cloud/DevOps/MLOps
    "AWS", "EC2", "S3", "Lambda", "VPC", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD", "MLFlow", "Kubeflow", "Airflow", "Tecton", "Luigi",

    #Misc
    "REST API", "GraphQL", "Flask", "FastAPI", "Docker Compose", "Pip", "Conda", "Jupyter", "VSCode"
]


structured_jobs = []
for idx, job in enumerate(jobs):
    # Split the job posting into lines and remove empty lines
    lines = job.splitlines()
    lines = [line.strip() for line in lines if line.strip()]

    if not lines:
        continue

    # Pull skills from job postings
    found_skills = extract_skills(job, soft_eng_skills)




    title, company = extract_title_company(job)

    if title is None or company is None:
        continue

    job_record = {
        "id": idx + 1,
        "title": title,
        "company": company,
        "skills": found_skills
    }

    structured_jobs.append(job_record)


with open("data/structured_jobs.json", "w", encoding="utf-8") as file:
    json.dump(structured_jobs, file, indent=2, ensure_ascii=False)

with open("data/structured_jobs.json", "r", encoding="utf-8") as f:
    structured_jobs = json.load(f)

skill_counter = Counter()
for job in structured_jobs:
    skill_counter.update(job.get("skills", []))

TOP_N = 15
print(f"Top {TOP_N} skills across {len(structured_jobs)} postings:\n")
for skill, count in skill_counter.most_common(TOP_N):
    print(f"{skill}: {count}")

zero_skill_jobs = sum(1 for job in structured_jobs if not job.get("skills"))
print(f"\nJobs with no skills extracted: {zero_skill_jobs}")


print(len(structured_jobs))

def read_text_file(path: str) -> str:

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p.resolve()}")
    return p.read_text(encoding="utf-8")

def normalize_text(text: str) -> str:

    # Standardize line endings
    t = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove common leftovers
    t = t.replace("&nbsp;", " ")

    # Convert tabs to spaces
    t = t.replace("\t", " ")

    # Strip each line and collapse internal whitespace
    lines = []
    for line in t.split("\n"):
        line = line.strip()
        line = re.sub(r"\s+", " ", line)
        lines.append(line)

    # Remove leading/trailing empty lines and collapse multiple blank lines
    cleaned_lines = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 1:
                cleaned_lines.append("")
        else:
            blank_run = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()

raw_resume = read_text_file("data/resume.txt")
resume_text = normalize_text(raw_resume)

print("Chars (raw):", len(raw_resume))
print("Chars (normalized):", len(resume_text))
print("\nPreview:\n", resume_text[:400])