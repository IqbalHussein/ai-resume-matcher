#Simple program designed to pull skills from a job posting
import json

with open("test_jobs.txt", "r", encoding="utf-8") as file:
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
    print(f"Job {idx+1} has {len(lines)} non-empty lines")

    # Pull skills from job postings
    found_skills = set()
    job_text = job.lower()
    for skill in soft_eng_skills:
        if skill.lower() in job_text:
            found_skills.add(skill)

    if found_skills:
        print(f"  Skills found: {', '.join(sorted(found_skills))}")
    else:
        print("  Skills found: None")

    title = lines[0]
    company = lines[1]

    job_record = {
        "id": idx + 1,
        "title": title,
        "company": company,
        "skills": sorted(found_skills)
    }

    structured_jobs.append(job_record)

if jobs and jobs[0].strip():
    # Print first line of every job
    first_job_lines = [l.strip() for l in jobs[0].splitlines() if l.strip()]
    if first_job_lines:
        print("FIRST LINE:", first_job_lines[0])
        if len(first_job_lines) > 1:
            print("SECOND LINE:", first_job_lines[1])

with open("data/structured_jobs.json", "w", encoding="utf-8") as file:
    json.dump(structured_jobs, file, indent=2, ensure_ascii=False)

print(len(structured_jobs))