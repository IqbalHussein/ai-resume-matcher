#Simple program designed to pull skills from a job posting
import json, re

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
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "SQL", "R", "Shell", "Bash",

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

    # Pull skills from job postings
    found_skills = set()
    job_text = job.lower()
    for skill in soft_eng_skills:
        if skill.lower() in job_text:
            found_skills.add(skill)


    title, company = extract_title_company(job)

    if title is None or company is None:
        continue

    if not lines:
        continue

    job_record = {
        "id": idx + 1,
        "title": title,
        "company": company,
        "skills": sorted(found_skills)
    }

    structured_jobs.append(job_record)


with open("data/structured_jobs.json", "w", encoding="utf-8") as file:
    json.dump(structured_jobs, file, indent=2, ensure_ascii=False)

print(len(structured_jobs))